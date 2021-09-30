from typing import List


class L1Event:
    data: str

class L1Transaction:
    data: str

class L1Block:
    block_hash: str
    base_fee: int
    block_number: int
    timestamp: int
    events: List[L1Event]
    txs: List[L1Transaction]

l1_blockchain: List[L1Block] = []

for i in range(100):
    events: List[L1Event] = [{ "data": "event 1 data" }, { "data": "event 2 data" }]
    txs: List[L1Event] = [{ "data": "tx 1 data" }]
    next_block: L1Block = {
        "block_hash": 'blockhash' + str(i),
        "base_fee": 'basefee' + str(i),
        "block_number": i,
        "timestamp": i,
        "events": events,
        "txs": txs
    }
    l1_blockchain.append(next_block)

print("Created a mock blockchain.")

print("Time to write a function which transforms each L1 block into some number of L2 blocks.")

