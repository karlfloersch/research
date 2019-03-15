from erc20_plasma_contract import Erc20Deposit
from utils import State, Commitment

def test_deposit(alice, erc20_ct, erc20_plasma_ct, ownership_predicate):
    # Deposit some funds
    erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})
    # Assert the balances have changed
    assert erc20_ct.balanceOf(alice.address) == 900
    assert erc20_ct.balanceOf(erc20_plasma_ct.address) == 100
    # Assert that we recorded the deposit and incremented total_deposits
    assert len(erc20_plasma_ct.claimable_ranges) == 1 and isinstance(next(iter(erc20_plasma_ct.claimable_ranges.values())), Erc20Deposit)
    assert erc20_plasma_ct.total_deposits == 100

def test_commitments(alice, bob, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit some funds
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})
    commit1_bob_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': bob.address})
    # Create the new state updates which we plan to commit
    state_bob_ownership = State(ownership_predicate, {'recipient': bob.address})
    state_alice_ownership = State(ownership_predicate, {'recipient': alice.address})
    # Create the commitment objects based on the states which will be included in plasma blocks
    commit2_alice_to_bob = Commitment(state_bob_ownership, commit0_alice_deposit.start, commit0_alice_deposit.end, 0)
    commit3_bob_to_alice = Commitment(state_alice_ownership, commit1_bob_deposit.start, commit1_bob_deposit.end, 0)
    # Add the commitments
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [commit2_alice_to_bob, commit3_bob_to_alice]})
    # Assert inclusion of our commitments
    assert erc20_plasma_ct.commitment_chain.validate_commitment(commit2_alice_to_bob, erc20_plasma_ct.address, None)
    assert erc20_plasma_ct.commitment_chain.validate_commitment(commit3_bob_to_alice, erc20_plasma_ct.address, None)
