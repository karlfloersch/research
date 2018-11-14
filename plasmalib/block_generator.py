from plasmalib.utils import Msg, to_bytes32
from random import randrange
import bisect
import time


class EphemDB():
    def __init__(self, kv=None):
        self.kv = kv or {}

    def get(self, k):
        return self.kv.get(k, None)

    def put(self, k, v):
        self.kv[k] = v

    def delete(self, k):
        del self.kv[k]

# Generate transactions
# total_deposits = 1000000
total_deposits = 10
txs = []
for i in range(5):
    start = randrange(total_deposits-1)
    offset = randrange(1, 5)
    if start + offset > total_deposits:
        start -= offset
    txs.append(Msg('0x', '0x', start, offset))

starts_and_ends = set()
starts_and_ends.add(0)
txs_by_start = dict()
start_time = time.time()
for tx in txs:
    starts_and_ends.add(tx.start)
    starts_and_ends.add(tx.start+tx.offset)
    if tx.start not in txs_by_start:
        txs_by_start[tx.start] = []
    txs_by_start[tx.start].append(tx)

list_of_starts_and_ends = sorted(starts_and_ends)
active_txs = []
buckets = []
for idx, i in enumerate(list_of_starts_and_ends):
    if i in txs_by_start:
        active_txs = active_txs + txs_by_start[i]
    active_txs = [tx for tx in active_txs if tx.start + tx.offset != i]
    if len(active_txs) == 0 and idx+1 != len(list_of_starts_and_ends):
        buckets.append((i, [Msg('0x01', '0x01', i, list_of_starts_and_ends[idx+1] - i)]))
    else:
        buckets.append((i, active_txs))
    # Remove all txs which should now be dead
    print('starts:', [tx.start for tx in active_txs])
    print('ends:', [tx.start + tx.offset for tx in active_txs])
    print('current value:', i)
    print("~~~~")

print('~~~\nTxs:')
print([(tx.start, tx.offset) for tx in txs])
print('~~~\nBuckets:')

for bucket in buckets:
    print(bucket[0], [(tx.start, tx.offset, tx.sender) for tx in bucket[1]])

# for tx in txs:
#     bisect.insort(starts, tx.start)
#     if tx.start not in txs_by_start:
#         txs_by_start[tx.start] = []
#     txs_by_start[tx.start].append(tx)
# tx_buckets = dict()
# for start in starts:
#     # Create buckets
#     for tx in txs_by_start[start]:
#         print(tx)

print("--- %s seconds ---" % (time.time() - start_time))
print('done')


# def find_pos_in_tree(max_value, index):

# num_tokens = 100

# print(find_pos_in_tree(num_tokens, 0))

# 50
# 100

# print(Msg)
# print(to_bytes32)
