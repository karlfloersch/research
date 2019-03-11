from erc20_plasma_contract import Erc20Deposit
from utils import State

def test_deposit(alice, erc20_ct, erc20_plasma_ct, transfer_predicate):
    # Deposit some funds
    erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})
    # Assert the balances have changed
    assert erc20_ct.balanceOf(alice.address) == 900
    assert erc20_ct.balanceOf(erc20_plasma_ct.address) == 100
    # Assert that we recorded the deposit and incremented total_deposits
    assert len(erc20_plasma_ct.deposits) == 1 and isinstance(erc20_plasma_ct.deposits[0], Erc20Deposit)
    assert erc20_plasma_ct.total_deposits == 1

def test_commitments(alice, bob, erc20_plasma_ct, transfer_predicate):
    # Deposit some funds
    state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})
    state1_bob_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': bob.address})
    # Create a tx which sends alice's coin to bob
    state2_alice_to_bob = State(state0_alice_deposit.coin_id, 0, transfer_predicate, {'recipient': bob.address})
    state3_bob_to_alice = State(state1_bob_deposit.coin_id, 0, transfer_predicate, {'recipient': alice.address})
    erc20_plasma_ct.add_commitment([state2_alice_to_bob, state3_bob_to_alice])
    # Assert inclusion of our txs
    assert state2_alice_to_bob in erc20_plasma_ct.commitments[0] and state3_bob_to_alice in erc20_plasma_ct.commitments[0]
