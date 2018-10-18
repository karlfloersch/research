from contract import PlasmaContract
from tx_tree_utils import EphemDB, fill_tx_list_with_notxs, get_sum_hash_of_tx, make_block_from_txs
import pprint
pp = pprint.PrettyPrinter(indent=4)

contract = PlasmaContract()
db = EphemDB()

block0_txs = [
    {'type:': 'send', 'contents': {'start': 1, 'offset': 4, 'owner': 'alice', 'to': 'alice'}, 'sig': 'sig'}
]
block0_full_txs = fill_tx_list_with_notxs(block0_txs)
block0_hash = make_block_from_txs(db, block0_full_txs)
pp.pprint(block0_full_txs)

block1_txs = [
    {'type:': 'send', 'contents': {'start': 2, 'offset': 1, 'owner': 'alice', 'to': 'bob'}, 'sig': 'sig'},
]
block1_full_txs = fill_tx_list_with_notxs(block1_txs)
block1_hash = make_block_from_txs(db, block1_full_txs)
pp.pprint(block1_full_txs)

# Add some blocks to our Plasma contract
contract.deposit('ETH', 10, 'alice')
contract.add_block(block0_hash)
contract.add_block(block1_hash)
contract.time += 5
# Start an exit referencing a spent coin
contract.exit('ETH', 1, 2, 'alice')
contract.time += 5
# Challenge the exit with Bob's tx -- coin 2 in block 2
contract.challenge_spent_coin(0, 2, 0, 'proof')
contract.refute_challenge(0, 0, 2, 1, 'proof')
contract.time += 15
contract.withdraw(0)
# print(contract.total_deposits)
# print(contract.blocks)
