import plyvel
from eth_utils import (
    int_to_big_endian,
    big_endian_to_int,
)
import time
import os
import rlp


class EphemDB():
    def __init__(self, kv=None):
        self.kv = kv or {}

    def get(self, k):
        return self.kv.get(k, None)

    def put(self, k, v):
        self.kv[k] = v

    def delete(self, k):
        del self.kv[k]


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
    def __init__(self, start, offset, owner):
        self.start = start
        self.offset = offset
        self.owner = owner


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
            total_deposits = b'\x00'
        deposit_start = total_deposits
        total_deposits = int_to_big_endian32(big_endian_to_int(total_deposits) + deposit_record.amount)
        # Add new deposit to the state and update total deposits
        wb = self.db.write_batch()
        self.store_deposit(deposit_start, deposit_record)
        self.db.put(b'total_deposits-' + int_to_big_endian8(deposit_record.token_id), total_deposits)
        wb.write()
        return True

    def store_deposit(self, start, deposit_record):
        self.store_range(deposit_record.recipient, start, int_to_big_endian32(deposit_record.amount), int_to_big_endian8(deposit_record.token_id))

    def store_tx(self, tx):
        self.store_range(tx.recipient, int_to_big_endian32(tx.start), int_to_big_endian32(tx.offset), int_to_big_endian8(tx.token_id))

    def store_range(self, owner, start, offset, token_id):
        self.db.put(owner + b'-' + token_id + b'-' + start, b'1')
        self.db.put(token_id + b'-' + start + b'-1offset', offset)
        self.db.put(token_id + b'-' + start + b'-2owner', owner)

    def add_tx(self, tx):
        # Now make sure the range is owned by the sender
        tx_lookup = int_to_big_endian8(tx.token_id) + b'-' + int_to_big_endian32(tx.start)
        if self.db.get(tx_lookup + b'-1') is not None:
            amount_key, recipient_key, last_tx_key = tx_lookup + b'-1', tx_lookup + b'-2', tx_lookup + b'-3'
        else:
            it = self.db.iterator(include_value=False)
            it.seek(tx_lookup)
            last_tx_key, recipient_key, amount_key = it.prev(), it.prev(), it.prev()
        print('Keys:', amount_key, recipient_key, last_tx_key)
        print('Values:', self.db.get(amount_key), self.db.get(recipient_key), self.db.get(last_tx_key))
        print(last_tx_key[2:])
        test = last_tx_key.split(b'-')
        print('this:', big_endian_to_int(test[1]))
        assert False

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
