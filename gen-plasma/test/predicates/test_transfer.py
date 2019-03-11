from utils import State
from predicates.transfer import TransferTransitionWitness

def test_submit_claim_on_deposit(alice, erc20_plasma_ct, transfer_predicate):
    state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})
    # Try submitting claim
    erc20_plasma_ct.submit_claim(state0_alice_deposit)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues) == 1

def test_submit_claim_on_transaction(alice, bob, erc20_plasma_ct, transfer_predicate):
    # Deposit and send a tx
    state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})  # Add deposit
    state1_alice_to_bob = State(state0_alice_deposit.coin_id, 0, transfer_predicate, {'recipient': bob.address})  # Create tx
    erc20_plasma_ct.add_commitment([state1_alice_to_bob])  # Add the tx to the first commitment
    # Try submitting claim
    erc20_plasma_ct.submit_claim(state1_alice_to_bob, 0)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues) == 1

def test_submit_dispute_on_deposit(alice, bob, erc20_plasma_ct, transfer_predicate):
    # Deposit and send a tx
    state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})  # Add deposit
    state1_alice_to_bob = State(state0_alice_deposit.coin_id, 0, transfer_predicate, {'recipient': bob.address})
    erc20_plasma_ct.add_commitment([state1_alice_to_bob])  # Add the tx to the first commitment
    transition_witness0_alice_to_bob = TransferTransitionWitness(alice.address, 0)
    # Try submitting claim on deposit
    deposit_claim = erc20_plasma_ct.submit_claim(state0_alice_deposit)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues[state1_alice_to_bob.coin_id]) == 1
    # Now bob disputes claim in the transfer settlement contract with the spend
    erc20_plasma_ct.dispute_claim(bob.address, deposit_claim, transition_witness0_alice_to_bob, state1_alice_to_bob)
    # Check the claim was deleted
    assert len(erc20_plasma_ct.claim_queues[state1_alice_to_bob.coin_id]) == 0

def test_invalid_tx_exit_queue_resolution(alice, mallory, erc20_plasma_ct, transfer_predicate, erc20_ct):
    # Deposit and commit to invalid state
    state0_alice_deposit = erc20_plasma_ct.deposit_ERC20(alice.address, 100, transfer_predicate, {'recipient': alice.address})  # Add deposit
    # Create invalid state
    state1_mallory_to_mallory = State(state0_alice_deposit.coin_id, 0, transfer_predicate, {'recipient': mallory.address})
    erc20_plasma_ct.add_commitment([state1_mallory_to_mallory])  # Add the invalid state to the first commitment
    # Submit a claim for the invalid state
    invalid_claim = erc20_plasma_ct.submit_claim(state1_mallory_to_mallory, 0)
    # Alice notices the invalid claim, and submits her own claim. Note that it is based on her deposit which is before the tx
    valid_claim = erc20_plasma_ct.submit_claim(state0_alice_deposit)
    # Wait for the dispute period to end.
    erc20_plasma_ct.eth.block_number += transfer_predicate.dispute_duration
    # Mallory attempts and fails to withdraw because there's another claim with priority
    try:
        erc20_plasma_ct.resolve_claim(mallory.address, invalid_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now alice withdraws
    erc20_plasma_ct.resolve_claim(alice.address, valid_claim)
    # Check that the balances have updated
    assert erc20_ct.balanceOf(alice.address) == 1000
    assert erc20_ct.balanceOf(erc20_plasma_ct.address) == 0
