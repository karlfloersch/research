from ethereum.utils import encode_hex
from contract import PlasmaContract
from tx_tree_utils import EphemDB, fill_tx_list_with_notxs, make_block_from_txs, get_proof_of_index, get_sum_hash_of_tx

import pprint
pp = pprint.PrettyPrinter(indent=4)

contract = PlasmaContract()
db = EphemDB()

# Tx array positions -- [parent_block, start, offset, to, from, signature]
block0_txs = [
    [0, 1, 4, 'alice', 'alice', 'sig'],
    [0, 8, 1, 'alice', 'alice', 'sig'],
    [0, 12, 2, 'alice', 'alice', 'sig']
]
block0_full_txs = fill_tx_list_with_notxs(block0_txs)
block0_hash = make_block_from_txs(db, block0_full_txs)
pp.pprint(block0_full_txs)

block1_tx_hash = get_sum_hash_of_tx(block0_txs[2])
block1_txs = [
    [1, 1, 4, 'bob', 'alice', 'sig']
]
block1_full_txs = fill_tx_list_with_notxs(block1_txs)
block1_hash = make_block_from_txs(db, block1_full_txs)
pp.pprint(block1_full_txs)

# Add some blocks to our Plasma contract
contract.deposit('ETH', 25, 'alice')
contract.add_block(block0_hash)
contract.add_block(block1_hash)
contract.time += 5
# Start a legit exit
contract.exit('ETH', 0, 2, 2, 'alice')
contract.time += 5
# Challenge the exit with Alice's tx -- coin 2 in block 0
challenge_coin_id = 2
spent_challenge_proof = get_proof_of_index(db, block0_hash, challenge_coin_id)
coin_challenge_proof = get_proof_of_index(db, block1_hash, challenge_coin_id)
for p in spent_challenge_proof:
    if p == spent_challenge_proof[-1]:
        print(p)
        break
    print(p[0])
    print(encode_hex(p[1]))
print('yolo')
# def challenge_spend(self, exit_index, coin_id, blocknumber_of_spend, exit_tx, exit_proof, spend_tx, spend_proof):
contract.challenge_spend(0, challenge_coin_id, 1, block1_txs[0], spent_challenge_proof, block1_txs[0], spent_challenge_proof)
assert False
contract.challenge_coin(0, challenge_coin_id, 0, block0_txs[2], spent_challenge_proof)
# Refute the challenge with Bob's tx -- coin challenge_coin_id in block 1
refute_proof = get_proof_of_index(db, block1_hash, challenge_coin_id)
contract.refute_challenge(0, 0, challenge_coin_id, 1, block1_txs[0], refute_proof)
contract.time += 15
# Withdraw the coin successfully!
contract.withdraw(0)
