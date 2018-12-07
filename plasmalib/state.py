import plyvel
from web3 import Web3
from plasmalib.utils import (
    int_to_big_endian8,
    int_to_big_endian32,
)
from eth_utils import (
    big_endian_to_int,
    decode_hex,
)
import time
import os
import rlp


TOTAL_DEPOSITS_PREFIX = b'total_deposits-'
OFFSET_SUFFIX = b'-1offset'
OWNER_SUFFIX = b'-2owner'
NONCE_SUFFIX = b'-nonce'

def get_total_deposits_key(token_id):
    assert type(token_id) == bytes
    return TOTAL_DEPOSITS_PREFIX + token_id

def get_start_to_offset_key(token_id, start):
    assert type(token_id) == bytes and type(start) == bytes
    return token_id + start + OFFSET_SUFFIX

def get_start_to_owner_key(token_id, start):
    assert type(token_id) == bytes and type(start) == bytes
    return token_id + start + OWNER_SUFFIX

def get_owner_to_nonce_key(owner):
    assert type(owner) == bytes
    return owner + NONCE_SUFFIX

def get_owner_to_start_key(owner, token_id, start):
    assert type(owner) == bytes and type(token_id) == bytes and type(start) == bytes
    return owner + token_id + start

class FileLog:
    def __init__(self, log_dir, backup_timeout):
        self.log_dir = log_dir
        self.tmp_log_path = os.path.join(log_dir, "tmp_log")
        try:
            os.remove(self.tmp_log_path)
        except Exception:
            print('No tmp log found')
        assert not os.path.isfile(self.tmp_log_path)
        os.makedirs(os.path.dirname(self.tmp_log_path), exist_ok=True)
        self.tmp_log = open(self.tmp_log_path, 'a')
        self.last_backup = time.time()
        self.backup_timeout = backup_timeout

    def add_record(self, record):
        self.tmp_log.write(rlp.encode(record))
        if time.time() - self.backup_timeout > self.last_backup:
            self.backup()

    def backup(self):
        self.tmp_log.flush()
        self.tmp_log.close()
        os.rename(self.tmp_log_path, os.path.join(self.log_dir, int(time.time())))
        self.tmp_log = open(self.tmp_log_path, 'a')


class RangeDBEntry:
    def __init__(self, owner, start, offset, token_id):
        # Convert and validate the parameters
        self.owner, self.start, self.offset, self.token_id = self.get_converted_parameters(owner, start, offset, token_id)
        # For convenience save the keys which we will use to store the range in the db
        self.start_lookup_key = self.token_id + self.start
        self.start_to_offset_key = self.start_lookup_key + OFFSET_SUFFIX
        self.start_to_owner_key = self.start_lookup_key + OWNER_SUFFIX
        self.owner_to_nonce_key = self.owner + NONCE_SUFFIX
        self.owner_to_start_key = self.owner + self.token_id + self.start
        # For convenience save the end
        self.end = self.token_id + int_to_big_endian32(big_endian_to_int(self.start) + big_endian_to_int(self.offset) - 1) + OFFSET_SUFFIX


class State:
    '''
    State object accepts txs, verifies that they are valid, and updates
    the leveldb database.
    '''
    def __init__(self, db_dir, tx_log_dir, create_if_missing=True, backup_timeout=60):
        self.db = plyvel.DB(db_dir, create_if_missing=create_if_missing)
        # self.wb = self.db.write_batch()
        # self.db = EphemDB()
        self.file_log = FileLog(tx_log_dir, backup_timeout)

    def add_deposit(self, recipient, token_id, amount):
        # Update total deposits
        total_deposits = self.db.get(get_total_deposits_key(int_to_big_endian8(token_id)))
        if total_deposits is None:
            total_deposits = b'\x00'*32
        deposit_start = big_endian_to_int(total_deposits)
        total_deposits = int_to_big_endian32(deposit_start + amount)
        # Begin write batch--data written to DB during write batch is all or nothing
        wb = self.db.write_batch()
        # Store the range
        self.store_range(recipient, token_id, deposit_start, amount)
        # Update total deposits
        self.db.put(b'total_deposits-' + int_to_big_endian8(token_id), total_deposits)
        # End write batch
        wb.write()
        return True

    def store_range(self, owner, token_id, start, offset):
        ''' Stores a range with the specified parameters.
            Note that all params other than `owner` are ints.
        '''
        owner, token_id, start, offset = self.get_converted_parameters(addresses=(owner,), bytes8s=(token_id,), bytes32s=(start, offset))
        # Put everything into the db
        if self.db.get(get_owner_to_nonce_key(owner)) is None:
            # If there's no nonce for the owner, add one
            self.db.put(get_owner_to_nonce_key(owner), int_to_big_endian8(0))
        self.db.put(get_owner_to_start_key(owner, token_id, start), b'1')
        self.db.put(get_start_to_offset_key(token_id, start), offset)
        self.db.put(get_start_to_owner_key(token_id, start), owner)

    def get_converted_parameters(self, addresses=(), bytes8s=(), bytes32s=()):
        converted = ()
        for a in addresses:
            if type(a) != bytes:
                a = decode_hex(a)
            assert Web3.isAddress(a)
            converted += (a,)
        for b8 in bytes8s:
            if type(b8) != bytes:
                b8 = int_to_big_endian8(b8)
            assert len(b8) == 8
            converted += (b8,)
        for b32 in bytes32s:
            if type(b32) != bytes:
                b32 = int_to_big_endian32(b32)
            assert len(b32) == 32
            converted += (b32,)
        return converted

    def get_ranges(self, token_id, start, end):
        token_id, start, end = self.get_converted_parameters(bytes8s=(token_id,), bytes32s=(start, end))
        it = self.db.iterator(include_value=False)
        token_lookup_key = token_id + start
        it.seek(token_lookup_key)
        last_key = next(it)
        # Move the iterator to the previous range
        while last_key[0:40] > token_lookup_key or OFFSET_SUFFIX not in last_key[40:]:
            last_key = it.prev()
        if last_key[0:40] != token_lookup_key:
            # If we entered the while loop, then we need to call next() to change the direction of the iterator
            last_key = next(it)
        affected_ranges = []
        end = token_id + end + OWNER_SUFFIX
        while end >= last_key:
            # Append to the affected_ranges list
            affected_ranges.append(last_key)
            last_key = next(it)
        return affected_ranges

    def verify_ranges_owner(self, ranges, owner):
        owner, = self.get_converted_parameters(addresses=(owner,))
        for r in ranges:
            r_owner = self.db.get(r)
            if owner != r_owner:
                return False
        return True

    def delete_ranges(self, ranges):
        for r in ranges:
            self.db.delete(r)

    def add_transaction(self, tx):
        txs = tx.serializableElements
        affected_ranges = self.get_ranges(txs[0].token_id, txs[0].start, txs[0].start + txs[0].offset - 1)
        print(affected_ranges)
        print(len(affected_ranges))
        print([big_endian_to_int(r[8:40]) for r in affected_ranges])

        # # Check that affected ranges are owned by the sender
        # assert self.validate_range_owner(affected_ranges, tx.sender)
        # # Shorten first range if needed
        # if new_db_entry.start_to_offset_key != affected_ranges[0]:
        #     # TODO: Add
        #     self.db.put(affected_ranges[0], int_to_big_endian32(tx.start - big_endian_to_int(affected_ranges[0][8:40])))
        #     print('setting new end offset to:', tx.start - big_endian_to_int(affected_ranges[0][8:40]))
        #     del affected_ranges[0:2]
        # # Shorten last range if needed
        # if len(affected_ranges) != 0 and new_db_entry.end != affected_ranges[-1]:
        #     self.db.put(affected_ranges[-2], int_to_big_endian32(tx.start + tx.offset))
        #     print('setting new start to:', tx.start + tx.offset)
        #     del affected_ranges[-2:]
        # print('Final Affected range start pos:', [big_endian_to_int(r[8:40]) for r in affected_ranges])
