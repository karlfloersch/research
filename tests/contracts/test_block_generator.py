from plasmalib.block_generator import create_tx_buckets, EphemDB, construct_tree
from plasmalib.transaction_validator import add_tx, add_deposit, subtract_range, add_range
from plasmalib.utils import Msg, Tx, Swap
from random import randrange
import time

class MockSig:
    def __init__(self):
        self.v = 0
        self.r = 0
        self.s = 0

class TxRange:
    def __init__(self, start, offset):
        self.start = start
        self.offset = offset

class TestNode:
    def __init__(self, db, account, friend_list):
        self.db = db
        self.account = account
        self.friend_list = friend_list

    def handle_response(self, responses):
        if self.account.address not in responses:
            return
        response = responses[self.account.address]
        # See if our tx went through!
        if response == 'FAILED':
            print('Oh no!')
            return

    def add_random_tx(self, msg_queue):
        ranges = self.db.get(self.account.address)
        if len(ranges) == 0:
            return 'No money!'
        tx_range_index = randrange(len(ranges)//2)*2
        if ranges[tx_range_index] == ranges[tx_range_index + 1]:
            start = ranges[tx_range_index]
        else:
            start = randrange(ranges[tx_range_index], ranges[tx_range_index + 1])
        max_offset = ranges[tx_range_index + 1] - start + 1
        if max_offset == 1:
            offset = 1
        else:
            offset = randrange(1, max_offset)
        raw_send = Msg(self.account.address, self.friend_list[randrange(len(self.friend_list))].address, start, offset)
        tx = Tx(raw_send, None, mock_signer)
        msg_queue.append(tx)


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

def process_tx(db, tx):
    add_tx_result = add_tx(db, tx)
    if add_tx_result is False:
        return tx.msg.sender, 'FAILED'
    return tx.msg.sender, add_tx_result

# def add_deposit(db, owner, amount, total_deposits):
def test_tx_validator(w3, tester, accts):
    print('starting...')
    db = EphemDB()
    nodes = []
    for a in accts:
        nodes.append(TestNode(db, a, accts))
    # Add a bunch of deposits
    max_deposit = 10
    for n in nodes:
        db.put(n.account.address, [])
    for i in range(1000):
        # Submit a deposit for a random node
        add_deposit(db, nodes[randrange(len(nodes))].account.address, randrange(1, max_deposit))
    # Tell the nodes what ranges they have
    for n in nodes:
        n.ranges = db.get(n.account.address)
    print(db.get('total_deposits'))
    print([(n.account.address, n.ranges) for n in nodes])
    responses = {}
    start_time = time.time()
    for i in range(1000):
        txs = []
        for n in nodes:
            n.handle_response(responses)
            n.add_random_tx(txs)
        responses = {}
        for t in txs:
            recipient, response = process_tx(db, t)
            responses[recipient] = response
    print("--- in %s seconds ---" % (time.time() - start_time))
    print('\nwhat\n')
    print([(n.account.address, n.ranges) for n in nodes])


    # db.put(accts[0].address, [0, 3, 7, 8, 10, 11])
    # db.put(accts[1].address, [4, 6, 9, 9, 12, 15])
    # valid_tx = Tx(Msg(accts[0].address, accts[1].address, 10, 2), None, mock_signer)
    # print('done')
    # print(db.get(accts[0].address))
    # print(db.get(accts[1].address))
    # print(add_tx(db, valid_tx))
    # print(db.get(accts[0].address))
    # print(db.get(accts[1].address))

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
