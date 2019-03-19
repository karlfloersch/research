from utils import State, Commitment
from predicates.ownership import OwnershipRevocationWitness

def test_submit_claim_on_deposit(alice, erc20_plasma_ct, ownership_predicate):
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})
    # Try submitting claim
    erc20_plasma_ct.claim_deposit(commit0_alice_deposit.end)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claims) == 1

def test_submit_claim_on_commitment(alice, bob, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and send a tx
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})  # Add deposit
    state_bob_ownership = State(ownership_predicate, {'recipient': bob.address})
    commit1_alice_to_bob = Commitment(state_bob_ownership, commit0_alice_deposit.start, commit0_alice_deposit.end, 0)  # Create commitment
    # Add the commit
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [commit1_alice_to_bob]})
    # Try submitting claim
    erc20_plasma_ct.claim_commitment(commit1_alice_to_bob, 'merkle proof', bob.address)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claims) == 1

def test_revoke_claim_on_deposit(alice, bob, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and send a tx
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})  # Add deposit
    state_bob_ownership = State(ownership_predicate, {'recipient': bob.address})
    commit1_alice_to_bob = Commitment(state_bob_ownership, commit0_alice_deposit.start, commit0_alice_deposit.end, 0)  # Create commitment
    # Add the commitment
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [commit1_alice_to_bob]})
    revocation_witness0_alice_to_bob = OwnershipRevocationWitness(commit1_alice_to_bob, alice.address, 'merkle proof')
    # Try submitting claim on deposit
    deposit_claim_id = erc20_plasma_ct.claim_deposit(100)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claims) == 1
    # Now bob revokes the claim with the spend inside the revocation witness
    erc20_plasma_ct.revoke_claim(10, deposit_claim_id, revocation_witness0_alice_to_bob)
    # Check the claim was deleted
    assert len(erc20_plasma_ct.claims) == 0


def test_challenge_claim_with_invalid_state(alice, mallory, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and commit to invalid state
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'recipient': alice.address})  # Add deposit
    state_mallory_ownership = State(ownership_predicate, {'recipient': mallory.address})
    invalid_commit1_alice_to_mallory = Commitment(state_mallory_ownership,
                                                  commit0_alice_deposit.start,
                                                  commit0_alice_deposit.end,
                                                  0)  # Create commitment
    # Add the commitment
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [invalid_commit1_alice_to_mallory]})
    # Submit a claim for the invalid state
    commitment_claim_id = erc20_plasma_ct.claim_commitment(invalid_commit1_alice_to_mallory, 'merkle proof', mallory.address)
    # Oh no! Alice notices bad behavior and attempts withdrawal of deposit state
    deposit_claim_id = erc20_plasma_ct.claim_deposit(commit0_alice_deposit.end)
    # Alice isn't letting that other claim go through. She challenges it with her deposit!
    challenge = erc20_plasma_ct.challenge_claim(deposit_claim_id, commitment_claim_id)
    # Verify that the challenge was recorded
    assert challenge is not None and len(erc20_plasma_ct.challenges) == 1




    # revocation_witness0_alice_to_bob = OwnershipRevocationWitness(commit1_alice_to_bob, alice.address, 'merkle proof')
    # # Try submitting claim on deposit
    # deposit_claim_id = erc20_plasma_ct.claim_deposit(100)
    # # Check the claim was recorded
    # assert len(erc20_plasma_ct.claims) == 1
    # # Now bob revokes the claim with the spend inside the revocation witness
    # erc20_plasma_ct.revoke_claim(10, deposit_claim_id, revocation_witness0_alice_to_bob)
    # # Check the claim was deleted
    # assert len(erc20_plasma_ct.claims) == 0




# def test_invalid_tx_exit_queue_resolution(alice, mallory, erc20_plasma_ct, ownership_predicate, erc20_ct):
#     # Deposit and commit to invalid state
#     state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, ownership_predicate, {'recipient': alice.address})  # Add deposit
#     # Create invalid state
#     state1_mallory_to_mallory = State(state0_alice_deposit.coin_id, 0, ownership_predicate, {'recipient': mallory.address})
#     erc20_plasma_ct.add_commitment([state1_mallory_to_mallory])  # Add the invalid state to the first commitment
#     # Submit a claim for the invalid state
#     invalid_claim = erc20_plasma_ct.submit_claim(state1_mallory_to_mallory, 0)
#     # Alice notices the invalid claim, and submits her own claim. Note that it is based on her deposit which is before the tx
#     valid_claim = erc20_plasma_ct.submit_claim(state0_alice_deposit)
#     # Wait for the dispute period to end.
#     erc20_plasma_ct.eth.block_number += ownership_predicate.dispute_duration
#     # Mallory attempts and fails to withdraw because there's another claim with priority
#     try:
#         erc20_plasma_ct.resolve_claim(mallory.address, invalid_claim)
#         throws = False
#     except Exception:
#         throws = True
#     assert throws
#     # Now alice withdraws
#     erc20_plasma_ct.resolve_claim(alice.address, valid_claim)
#     # Check that the balances have updated
#     assert erc20_ct.balanceOf(alice.address) == 1000
#     assert erc20_ct.balanceOf(erc20_plasma_ct.address) == 0
