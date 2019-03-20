from utils import State, Commitment
from predicates.ownership import OwnershipRevocationWitness

def test_submit_claim_on_deposit(alice, erc20_plasma_ct, ownership_predicate):
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'owner': alice.address})
    # Try submitting claim
    erc20_plasma_ct.claim_deposit(commit0_alice_deposit.end)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claims) == 1

def test_submit_claim_on_commitment(alice, bob, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and send a tx
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'owner': alice.address})  # Add deposit
    state_bob_ownership = State(ownership_predicate, {'owner': bob.address})
    commit1_alice_to_bob = Commitment(state_bob_ownership, commit0_alice_deposit.start, commit0_alice_deposit.end, 0)  # Create commitment
    # Add the commit
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [commit1_alice_to_bob]})
    # Try submitting claim
    claim_id = erc20_plasma_ct.claim_commitment(commit1_alice_to_bob, 'merkle proof', bob.address)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claims) == 1
    # Now increment the eth block to the redeemable block
    erc20_plasma_ct.eth.block_number = erc20_plasma_ct.claims[claim_id].eth_block_redeemable
    # Finally try withdrawing the money!
    erc20_plasma_ct.redeem_claim(claim_id, commit1_alice_to_bob.end)
    # Check bob's balance!
    assert erc20_plasma_ct.erc20_contract.balanceOf(bob.address) == 1100  # 1100 comes from bob having been sent 100 & already having 1000

def test_revoke_claim_on_deposit(alice, bob, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and send a tx
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'owner': alice.address})  # Add deposit
    state_bob_ownership = State(ownership_predicate, {'owner': bob.address})
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
    # Check the claim was revoked
    assert erc20_plasma_ct.claims[deposit_claim_id].is_revoked

def test_challenge_claim_with_invalid_state(alice, mallory, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and commit to invalid state
    commit0_alice_deposit = erc20_plasma_ct.deposit(alice.address, 100, ownership_predicate, {'owner': alice.address})  # Add deposit
    # Check that alice's balance was reduced
    assert erc20_plasma_ct.erc20_contract.balanceOf(alice.address) == 900
    # Uh oh! Malory creates an invalid state & commits it!!!
    state_mallory_ownership = State(ownership_predicate, {'owner': mallory.address})
    invalid_commit1_alice_to_mallory = Commitment(state_mallory_ownership,
                                                  commit0_alice_deposit.start,
                                                  commit0_alice_deposit.end,
                                                  0)  # Create commitment
    # Add the commitment
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [invalid_commit1_alice_to_mallory]})
    # Submit a claim for the invalid state
    invalid_commitment_claim_id = erc20_plasma_ct.claim_commitment(invalid_commit1_alice_to_mallory, 'merkle proof', mallory.address)
    # Oh no! Alice notices bad behavior and attempts withdrawal of deposit state
    deposit_claim_id = erc20_plasma_ct.claim_deposit(commit0_alice_deposit.end)
    # Alice isn't letting that other claim go through. She challenges it with her deposit!
    challenge = erc20_plasma_ct.challenge_claim(deposit_claim_id, invalid_commitment_claim_id)
    # Verify that the challenge was recorded
    assert challenge is not None and len(erc20_plasma_ct.challenges) == 1
    # Fast forward in time until the eth block allows the claim to be redeemable
    erc20_plasma_ct.eth.block_number = erc20_plasma_ct.claims[invalid_commitment_claim_id].eth_block_redeemable
    # Mallory attempts and fails to withdraw because there's another claim with priority
    try:
        erc20_plasma_ct.redeem_claim(mallory.address, invalid_commit1_alice_to_mallory.end)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now instead alice withdraws
    erc20_plasma_ct.redeem_claim(deposit_claim_id, erc20_plasma_ct.claims[deposit_claim_id].commitment.end)
    # Check that alice was sent her money!
    assert erc20_plasma_ct.erc20_contract.balanceOf(alice.address) == 1000

def test_redeem_challenged_claim(alice, mallory, operator, erc20_plasma_ct, ownership_predicate):
    # Deposit and then submit an invalid challenge
    commit0_mallory_deposit = erc20_plasma_ct.deposit(mallory.address, 100, ownership_predicate, {'owner': mallory.address})  # Add deposit
    # Create a new state & commitment for alice ownership
    state_alice_ownership = State(ownership_predicate, {'owner': alice.address})
    commit1_mallory_to_alice = Commitment(state_alice_ownership, commit0_mallory_deposit.start, commit0_mallory_deposit.end, 0)  # Create commitment
    # Add the commit
    erc20_plasma_ct.commitment_chain.commit_block(operator.address, {erc20_plasma_ct.address: [commit1_mallory_to_alice]})
    # Now alice wants to withdraw, so submit a new claim on the funds
    claim_id = erc20_plasma_ct.claim_commitment(commit1_mallory_to_alice, 'merkle proof', alice.address)
    # Uh oh! Mallory decides to withdraw and challenge the claim
    revoked_claim_id = erc20_plasma_ct.claim_deposit(commit0_mallory_deposit.end)
    challenge_id = erc20_plasma_ct.challenge_claim(revoked_claim_id, claim_id)
    # This revoked claim is then swiftly canceled by alice
    revocation_witness0_mallory_to_alice = OwnershipRevocationWitness(commit1_mallory_to_alice, mallory.address, 'merkle proof')
    erc20_plasma_ct.revoke_claim(10, revoked_claim_id, revocation_witness0_mallory_to_alice)
    # Remove the challenge for the revoked claim
    erc20_plasma_ct.remove_challenge(challenge_id)
    # Increment the eth block number
    erc20_plasma_ct.eth.block_number = erc20_plasma_ct.claims[claim_id].eth_block_redeemable
    # Now alice can withdraw!
    erc20_plasma_ct.redeem_claim(claim_id, erc20_plasma_ct.claims[claim_id].commitment.end)
    # Check that alice was sent her money!
    assert erc20_plasma_ct.erc20_contract.balanceOf(alice.address) == 1100
