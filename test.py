from contract import PlasmaContract
from tx_tree_utils import EphemDB, fill_tx_list_with_notxs, make_block_from_txs, get_proof_of_index, get_sum_hash_of_tx
import pprint
pp = pprint.PrettyPrinter(indent=4)

contract = PlasmaContract()
db = EphemDB()

block0_txs = [
    {'type:': 'send', 'contents': {'start': 1, 'offset': 4, 'owner': 'alice', 'to': 'alice'}, 'sig': 'sig'},
    {'type:': 'send', 'contents': {'start': 8, 'offset': 1, 'owner': 'alice', 'to': 'alice'}, 'sig': 'sig'},
    {'type:': 'send', 'contents': {'start': 12, 'offset': 2, 'owner': 'alice', 'to': 'alice'}, 'sig': 'sig'}
]
block0_full_txs = fill_tx_list_with_notxs(block0_txs)
block0_hash = make_block_from_txs(db, block0_full_txs)
pp.pprint(block0_full_txs)

block1_tx_hash = get_sum_hash_of_tx(block0_txs[2])
block1_txs = [
    {'type:': 'send', 'contents': {'prev_tx': str(block1_tx_hash), 'start': 12, 'offset': 2, 'owner': 'alice', 'to': 'bob'}, 'sig': 'sig'}
]
block1_full_txs = fill_tx_list_with_notxs(block1_txs)
block1_hash = make_block_from_txs(db, block1_full_txs)
pp.pprint(block1_full_txs)

# Add some blocks to our Plasma contract
contract.deposit('ETH', 25, 'alice')
contract.add_block(block0_hash)
contract.add_block(block1_hash)
contract.time += 5
# Start an exit referencing a spent coin
contract.exit('ETH', 12, 2, 'bob')
contract.time += 5
# Challenge the exit with Alice's tx -- coin 2 in block 0
challenge_coin_id = 12
challenge_proof = get_proof_of_index(db, block0_hash, challenge_coin_id)
pp.pprint(challenge_proof)
contract.challenge_coin(0, challenge_coin_id, 0, block0_txs[2], challenge_proof)
# Refute the challenge with Bob's tx -- coin challenge_coin_id in block 1
refute_proof = get_proof_of_index(db, block1_hash, challenge_coin_id)
contract.refute_challenge(0, 0, challenge_coin_id, 1, block1_txs[0], refute_proof)
contract.time += 15
# Withdraw the coin successfully!
contract.withdraw(0)
