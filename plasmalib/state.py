import plyvel
from web3 import Web3
from eth_utils import (
    int_to_big_endian,
    big_endian_to_int,
)
import time
import os
import rlp


class FileLog:
    def __init__(self, log_dir, backup_timeout):
        self.log_dir = log_dir
        self.tmp_log_path = os.path.join(log_dir, "tmp_log")
        os.remove(self.tmp_log_path)
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

def int_to_big_endian32(val):
    return int_to_big_endian(val).rjust(32, b'\0')

def int_to_big_endian8(val):
    return int_to_big_endian(val).rjust(8, b'\0')


class RangeDBEntry:
    def __init__(self, owner, start, offset, token_id):
        # Convert and validate the parameters
        self.owner, self.start, self.offset, self.token_id = self.get_converted_parameters(owner, start, offset, token_id)
        # For convenience save the keys which we will use to store the range in the db
        self.start_lookup_key = self.token_id + self.start
        self.start_to_offset_key = self.start_lookup_key + b'-1offset'
        self.start_to_owner_key = self.start_lookup_key + b'-2owner'
        self.owner_to_nonce_key = self.owner + b'-nonce'
        self.owner_to_start_key = self.owner + self.token_id + self.start
        # For convenience save the end
        self.end = self.token_id + int_to_big_endian32(big_endian_to_int(self.start) + big_endian_to_int(self.offset) - 1) + b'-2owner'

    def get_converted_parameters(self, owner, start, offset, token_id):
        if type(start) != bytes:
            start = int_to_big_endian32(start)
        if type(offset) != bytes:
            offset = int_to_big_endian32(offset)
        if type(token_id) != bytes:
            token_id = int_to_big_endian8(token_id)
        assert Web3.isAddress(owner)
        assert len(start) == len(offset) == 32
        assert len(token_id) == 8
        return (owner, start, offset, token_id)

    def store_range(self, db):
        # Put everything into the db
        if db.get(self.owner_to_nonce_key) is None:
            # If there's no nonce for the owner, add one
            db.put(self.owner_to_nonce_key, int_to_big_endian8(0))
        db.put(self.owner_to_start_key, b'1')
        db.put(self.start_to_offset_key, self.offset)
        db.put(self.start_to_owner_key, self.owner)


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

    def add_deposit(self, deposit_record):
        # Update total deposits
        total_deposits = self.db.get(b'total_deposits-' + int_to_big_endian8(deposit_record.token_id))
        if total_deposits is None:
            total_deposits = b'\x00'*32
        deposit_start = total_deposits
        total_deposits = int_to_big_endian32(big_endian_to_int(total_deposits) + deposit_record.amount)
        # Create a new range entry for the deposit
        new_db_entry = RangeDBEntry(deposit_record.recipient, deposit_start, deposit_record.amount, deposit_record.token_id)
        # Begin write batch--data written to DB during write batch is all or nothing
        wb = self.db.write_batch()
        # Store the range
        new_db_entry.store_range(self.db)
        # Update total deposits
        self.db.put(b'total_deposits-' + int_to_big_endian8(deposit_record.token_id), total_deposits)
        # End write batch
        wb.write()
        return True

    def add_tx(self, tx):
        # Check nonce
        assert self.db.get(tx.sender + b'-nonce') == int_to_big_endian8(tx.nonce)
        # Create a db entry for the tx
        new_db_entry = RangeDBEntry(tx.recipient, tx.start, tx.offset, tx.token_id)
        # Get affected ranges
        affected_ranges = self.get_affected_ranges(new_db_entry)
        print('Affected ranges:', affected_ranges)
        print('Affected range start pos:', [big_endian_to_int(r[8:40]) for r in affected_ranges])
        # Check that affected ranges are owned by the sender
        assert self.validate_range_owner(affected_ranges, tx.sender)
        # Shorten first range if needed
        if new_db_entry.start_to_offset_key != affected_ranges[0]:
            # TODO: Add
            self.db.put(affected_ranges[0], int_to_big_endian32(tx.start - big_endian_to_int(affected_ranges[0][8:40])))
            print('setting new end offset to:', tx.start - big_endian_to_int(affected_ranges[0][8:40]))
            print(affected_ranges[0:2])
            del affected_ranges[0:2]
        # Shorten last range if needed
        if len(affected_ranges) != 0 and new_db_entry.end != affected_ranges[-1]:
            self.db.put(affected_ranges[-2], int_to_big_endian32(tx.start + tx.offset))
            print('setting new start to:', tx.start + tx.offset)
            del affected_ranges[-2:]
        print('Final Affected range start pos:', [big_endian_to_int(r[8:40]) for r in affected_ranges])

    def delete_ranges(ranges):
        # TODO: Implement
        pass

    def validate_range_owner(self, ranges, owner):
        # for r in ranges[1::2]:
        #     if self.db.get(r) != owner:
        #         return False
        return True

    def get_affected_ranges(self, db_entry):
        it = self.db.iterator(include_value=False)
        it.seek(db_entry.start_lookup_key)
        last_key = next(it)
        # Check if we need to move the iterator back to the previous range
        if db_entry.start_to_owner_key < last_key:
            it.prev()
            it.prev()
            it.prev()
        else:
            print('we are equal!')
        affected_ranges = []
        last_key = next(it)
        while db_entry.end >= last_key:
            # Append to the affected_ranges list
            affected_ranges.append(last_key)
            last_key = next(it)
        return affected_ranges

    def delete_ranges(self, it, end):
        db_entry = it.next()
        while db_entry.find(end) == -1:
            self.db.delete(db_entry)
            db_entry = it.next()
        # Delete the final entry
        self.db.delete(db_entry)
        self.db.delete(it.next())
        self.db.delete(it.next())

        pass
        # Start from the first tx

#         sender_ranges = db.get(tx.sender)
#         tx_start = tx.start
#         tx_end = tx.start + tx.offset - 1
#         # Subtract ranges from sender range list and store
#         if not subtract_range(sender_ranges, tx_start, tx_end):
#             return False
#         db.put(tx.sender, sender_ranges)
#         # After having deleted the sender ranges,
#         # Add ranges to recipient range list and store
#         recipient_ranges = db.get(tx.recipient)
#         add_range(recipient_ranges, tx_start, tx_end)
#         db.put(tx.recipient, recipient_ranges)
