import pytest
from utils import State
from predicates.multisig import MultiSigTransitionWitness, MultiSigPredicate

@pytest.fixture
def multisig_predicate(erc20_plasma_ct):
    return MultiSigPredicate(erc20_plasma_ct)

def skip_test_submit_claim_on_deposit(alice, bob, charlie, erc20_plasma_ct, multisig_predicate):
    state0_alice_and_bob_deposit = erc20_plasma_ct.deposit_ERC20(alice.address,
                                                                 100,
                                                                 multisig_predicate,
                                                                 {'recipient': [alice.address, bob.address]})
    # Try submitting claim
    erc20_plasma_ct.submit_claim(state0_alice_and_bob_deposit)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues) == 1

def skip_test_submit_claim_on_transaction(alice, bob, charlie, erc20_plasma_ct, multisig_predicate):
    # Deposit and send a tx
    state0_alice_and_bob_deposit = erc20_plasma_ct.deposit_ERC20(alice.address,
                                                                 100,
                                                                 multisig_predicate,
                                                                 {'recipient': [alice.address, bob.address]})
    state1_alice_and_bob = State(state0_alice_and_bob_deposit.coin_id,
                                 0,
                                 multisig_predicate,
                                 {'recipient': [charlie.address]})
    erc20_plasma_ct.add_commitment([state1_alice_and_bob])  # Add the tx to the first commitment
    # Try submitting claim
    erc20_plasma_ct.submit_claim(state1_alice_and_bob, 0)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues) == 1

def skip_test_submit_dispute_on_deposit(alice, bob, charlie, erc20_plasma_ct, multisig_predicate):
    # Deposit and send a tx
    state0_alice_and_bob_deposit = erc20_plasma_ct.deposit_ERC20(alice.address,
                                                                 100,
                                                                 multisig_predicate,
                                                                 {'recipient': [alice.address, bob.address]})
    state1_alice_and_bob = State(state0_alice_and_bob_deposit.coin_id,
                                 0,
                                 multisig_predicate,
                                 {'recipient': [charlie.address]})
    erc20_plasma_ct.add_commitment([state1_alice_and_bob])  # Add the tx to the first commitment
    # Create witness based on this commitment
    transition_witness0_alice_and_bob = MultiSigTransitionWitness([alice.address, bob.address], 0)
    # Try submitting claim on deposit
    deposit_claim = erc20_plasma_ct.submit_claim(state0_alice_and_bob_deposit)
    # Check the claim was recorded
    assert len(erc20_plasma_ct.claim_queues[state1_alice_and_bob.coin_id]) == 1
    # Now bob disputes claim with the spend
    erc20_plasma_ct.dispute_claim(bob.address, deposit_claim, transition_witness0_alice_and_bob, state1_alice_and_bob)
    # Check the claim was deleted
    assert len(erc20_plasma_ct.claim_queues[state1_alice_and_bob.coin_id]) == 0

def skip_test_invalid_tx_exit_queue_resolution(alice, bob, mallory, erc20_plasma_ct, multisig_predicate, erc20_ct):
    # Deposit and commit to an invalid state
    state0_alice_and_bob_deposit = erc20_plasma_ct.deposit_ERC20(alice.address,
                                                                 100,
                                                                 multisig_predicate,
                                                                 {'recipient': [alice.address, bob.address]})
    state1_mallory_to_mallory = State(state0_alice_and_bob_deposit.coin_id,
                                      0,
                                      multisig_predicate,
                                      {'recipient': [mallory.address]})
    erc20_plasma_ct.add_commitment([state1_mallory_to_mallory])  # Add the invalid tx to the first commitment
    # Submit a claim for the invalid state
    invalid_claim = erc20_plasma_ct.submit_claim(state1_mallory_to_mallory, 0)
    # Alice notices the invalid claim, and submits her own claim. Note that it is based on her deposit which is before the tx
    valid_claim = erc20_plasma_ct.submit_claim(state0_alice_and_bob_deposit)
    # Wait for the dispute period to end.
    erc20_plasma_ct.eth.block_number += multisig_predicate.dispute_duration
    # Mallory attempts and fails to withdraw because there's another claim with priority
    try:
        erc20_plasma_ct.resolve_claim(mallory.address, invalid_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now alice and bob agree to send the money to a new on-chain multisig
    erc20_plasma_ct.resolve_claim(alice.address, valid_claim, ([alice.address, bob.address], 'on chain multisig address'))
    # Check that the balances have updated
    assert erc20_ct.balanceOf('on chain multisig address') == 100
    assert erc20_ct.balanceOf(erc20_plasma_ct.address) == 0
