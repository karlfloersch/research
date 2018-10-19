from tx_tree_utils import EphemDB, fill_tx_list_with_notxs, make_block_from_txs, get_proof_of_index, get_sum_hash_of_tx
import pprint
pp = pprint.PrettyPrinter(indent=4)

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


def test_plasma(w3, plasma_contract, pad_bytes32):
    a0, a1 = w3.eth.accounts[:2]
    plasma_contract.deposit_eth(transact={'value': 100})
    plasma_contract.deposit_eth(transact={'value': 100})
    assert plasma_contract.total_deposits(pad_bytes32('ETH')) == 200
    assert plasma_contract.next_deposit_id() == 2
    # Add block0 and 1
    plasma_contract.add_block(block0_hash, transact={})
    plasma_contract.add_block(block1_hash, transact={})
    assert plasma_contract.next_blocknumber() == 2
    assert plasma_contract.blocks(1) == block1_hash
    # Attempt to exit
    plasma_contract.exit(pad_bytes32('ETH'), 12, 2, a0, transact={})
    assert plasma_contract.next_exit_id() == 1
    # TODO: Add challenge coin
    # Challenge exit
    # challenge_coin_id = 12
    # challenge_proof = get_proof_of_index(db, block0_hash, challenge_coin_id)
    # plasma_contract.challenge_coin(0, challenge_coin_id, 0, block0_txs[2], challenge_proof)

    # assert plasma_contract.name() == pad_bytes32('OMG Token')
    # assert plasma_contract.symbol() == pad_bytes32('OMG')
    # assert plasma_contract.decimals() == 18
    # assert plasma_contract.totalSupply() == 100000*10**18
    # assert plasma_contract.balanceOf(a0) == 100000*10**18
    # plasma_contract.transfer(a1, 1*10**18, transact={})
    # assert plasma_contract.balanceOf(a0) == 100000*10**18 - 1*10**18
    # assert plasma_contract.balanceOf(a1) == 1*10**18
