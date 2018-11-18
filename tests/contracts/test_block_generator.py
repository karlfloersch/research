from plasmalib.block_generator import create_tx_buckets, EphemDB, construct_tree
from plasmalib.transaction_validator import add_tx, subtract_range, add_range
from plasmalib.utils import Msg, Tx, Swap
from random import randrange
import time

class MockSig:
    def __init__(self):
        self.v = 0
        self.r = 0
        self.s = 0

def mock_signer(msg):
    return MockSig()

# Generates a swap which swaps a bunch of coins in a contiguous range. eg. <----$$&&&@@@((---->
def generate_swap(num_txs, total_deposits, max_range, accts):
    # Make sure that the swap doesn't try to swap more tokens than exist.
    assert total_deposits - max_range*num_txs > 0
    swap_msgs = []
    start_counter = randrange(0, total_deposits - max_range*num_txs)
    for i in range(num_txs):
        sender = accts[randrange(10)]
        recipient = accts[randrange(10)]
        offset = randrange(1, max_range)
        swap_msgs.append(Msg(sender.address, recipient.address, start_counter, offset))
        start_counter += offset
    swap = Swap(swap_msgs)
    txs = []
    for msg in swap_msgs:
        txs.append(Tx(msg, swap, mock_signer))
    return txs

def generate_txs(num_txs, num_swaps, total_deposits, max_range, accts):
    assert max_range < total_deposits
    txs = []
    while num_swaps > 8:
        # Generate some swaps
        swap_count = randrange(2, 8)
        txs += generate_swap(swap_count, total_deposits, max_range, accts)
        num_swaps -= swap_count
    for i in range(num_txs):
        # Generate normal txs
        start = randrange(total_deposits - max_range)
        offset = randrange(1, max_range)
        sender = accts[randrange(10)]
        recipient = accts[randrange(10)]
        msg = Msg(sender.address, recipient.address, start, offset)
        txs.append(Tx(msg, None, mock_signer))
    return txs

def test_subtract_range():
    # Test subtracting a bunch of ranges
    range_list = [0, 3, 6, 10, 15, 17, 18, 18]
    subtract_range(range_list, 0, 3)
    assert range_list == [6, 10, 15, 17, 18, 18]
    subtract_range(range_list, 18, 18)
    assert range_list == [6, 10, 15, 17]
    subtract_range(range_list, 7, 7)
    assert range_list == [15, 17, 6, 6, 8, 10]
    subtract_range(range_list, 15, 17)
    assert range_list == [6, 6, 8, 10]
    subtract_range(range_list, 6, 6)
    assert range_list == [8, 10]
    subtract_range(range_list, 9, 9)
    assert range_list == [8, 8, 10, 10]
    subtract_range(range_list, 8, 8)
    assert range_list == [10, 10]
    subtract_range(range_list, 10, 10)
    assert range_list == []

def test_add_range():
    # Test adding a bunch of ranges
    range_list = [0, 1, 6, 10, 15, 17, 20, 20]
    add_range(range_list, 5, 5)
    assert range_list == [0, 1, 15, 17, 20, 20, 5, 10]
    add_range(range_list, 3, 3)
    assert range_list == [0, 1, 15, 17, 20, 20, 5, 10, 3, 3]
    add_range(range_list, 2, 2)
    assert range_list == [15, 17, 20, 20, 5, 10, 0, 3]
    add_range(range_list, 4, 4)
    assert range_list == [15, 17, 20, 20, 0, 10]
    add_range(range_list, 18, 19)
    assert range_list == [0, 10, 15, 20]
    add_range(range_list, 11, 14)
    assert range_list == [0, 20]

def test_tx_validator(w3, tester, accts):
    db = EphemDB()
    db.put(accts[0].address, [0, 3, 7, 8, 10, 11])
    db.put(accts[1].address, [4, 6, 9, 9, 12, 15])
    valid_tx = Tx(Msg(accts[0].address, accts[1].address, 10, 2), None, mock_signer)
    print('done')
    print(db.get(accts[0].address))
    print(db.get(accts[1].address))
    print(add_tx(db, valid_tx))
    print(db.get(accts[0].address))
    print(db.get(accts[1].address))

def test_block_generator(w3, tester, accts):
    db = EphemDB()
    # Generate transactions
    total_deposits = 10000
    total_txs = 1000
    txs = generate_txs(total_txs, 500, total_deposits, 10, accts)

    start_time = time.time()
    buckets = create_tx_buckets(db, txs)
    root_hash = construct_tree(db, [bucket.tx_merkle_tree_root_hash for bucket in buckets])

    print('~~~\nTxs:')
    print([(tx.start, tx.offset, tx.is_swap) for tx in txs])
    print('~~~\nBuckets:')

    for bucket in buckets:
        print(bucket.start, [(tx.start, tx.offset, tx.is_swap) for tx in bucket.txs])
    print('Committing block root hash:', root_hash)
    print(int.from_bytes(root_hash[24:], byteorder='big'))
    print('Processed', total_txs, 'transactions')
    print("--- in %s seconds ---" % (time.time() - start_time))

    print('done')
