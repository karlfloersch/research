from typing import List

class Event:
    data: str

class Transaction:
    data: str

class Block:
    block_hash: str
    base_fee: int
    block_number: int
    timestamp: int
    events: List[Event]
    txs: List[Transaction]