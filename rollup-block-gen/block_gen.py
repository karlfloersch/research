from typing import List

class DepositFeed:
    pass


class UserDeposit:
    is_eoa:       bool
    l1_tx_origin:  str
    target:      str
    data:        bytes

class SequencerBlock:
    is_eoa:       bool
    l1_tx_origin:  str
    target:      str
    data:        bytes

class SequencerBatch:
    is_eoa:       bool
    l1_tx_origin:  str
    target:      str
    data:        bytes

class EthereumBlock:
    block_hash: str
    base_fee: int
    block_number: int
    timestamp: int
    user_deposits: UserDeposit
    sequencer_batches: UserDeposit

mainnet_blockchain: List[EthereumBlock] = []

for i in range(100):
    user_deposit: UserDeposit = {
        "is_eoa": True,
        "l1_tx_origin": "da tx origin",
        "target": "da target",
        "data": b"da data"
    }
    next_block: EthereumBlock = {
        "block_hash": 'blockhash' + str(i),
        "base_fee": 'basefee' + str(i),
        "block_number": i,
        "timestamp": i,
        "user_deposits": [user_deposit]
    }
    mainnet_blockchain.append(next_block)

