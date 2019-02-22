import pytest
from settlement_contracts.multisig import MultiSigTransaction, MultiSigSettlementContract

@pytest.fixture
def multisig_settlement_ct(erc20_settlement_ct):
    return MultiSigSettlementContract(erc20_settlement_ct)

def test_submit_claim_on_transaction(alice, bob, charlie, erc20_settlement_ct, multisig_settlement_ct):
    # Deposit and send a tx
    alice_and_bob_deposit = erc20_settlement_ct.deposit_ERC20(alice.address,
                                                              100,
                                                              multisig_settlement_ct,
                                                              {'recipients': [alice.address, bob.address]})
    tx0_alice_and_bob = MultiSigTransaction(alice_and_bob_deposit.coin_id,
                                            0,
                                            [alice.address, bob.address],
                                            charlie.address,
                                            multisig_settlement_ct,
                                            {})
    erc20_settlement_ct.add_commitment([tx0_alice_and_bob])  # Add the tx to the first commitment
    # Try submitting claim
    erc20_settlement_ct.submit_claim(transaction=tx0_alice_and_bob)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues) == 1

def test_submit_dispute_on_deposit(alice, bob, charlie, erc20_settlement_ct, multisig_settlement_ct):
    # Deposit and send a tx
    alice_and_bob_deposit = erc20_settlement_ct.deposit_ERC20(alice.address,
                                                              100,
                                                              multisig_settlement_ct,
                                                              {'recipient': [alice.address, bob.address]})
    tx0_alice_and_bob = MultiSigTransaction(alice_and_bob_deposit.coin_id,
                                            0,
                                            [alice.address, bob.address],
                                            charlie.address,
                                            multisig_settlement_ct,
                                            {})
    erc20_settlement_ct.add_commitment([tx0_alice_and_bob])  # Add the tx to the first commitment
    # Try submitting claim on deposit
    deposit_claim = erc20_settlement_ct.submit_claim(deposit=alice_and_bob_deposit)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_and_bob.coin_id]) == 1
    # Alice attempts to call dispute directly & fails (can only be called by settlement contract
    try:
        erc20_settlement_ct.dispute_claim(alice.address, deposit_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now bob disputes claim in the transfer settlement contract with the spend
    multisig_settlement_ct.dispute_claim(deposit_claim, tx0_alice_and_bob)
    # Check the claim was deleted
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_and_bob.coin_id]) == 0

def test_invalid_tx_exit_queue_resolution(alice, bob, mallory, erc20_settlement_ct, multisig_settlement_ct, erc20_ct):
    # Deposit and send an invalid transaction
    alice_and_bob_deposit = erc20_settlement_ct.deposit_ERC20(alice.address,
                                                              100,
                                                              multisig_settlement_ct,
                                                              {'recipient': [alice.address, bob.address]})
    tx0_mallory_to_mallory = MultiSigTransaction(alice_and_bob_deposit.coin_id,
                                                 0,
                                                 [mallory.address],
                                                 [mallory.address],
                                                 multisig_settlement_ct,
                                                 {})
    erc20_settlement_ct.add_commitment([tx0_mallory_to_mallory])  # Add the invalid tx to the first commitment
    # Submit a claim for the invalid transaction
    invalid_claim = erc20_settlement_ct.submit_claim(transaction=tx0_mallory_to_mallory)
    # Alice notices the invalid claim, and submits her own claim. Note that it is based on her deposit which is before the tx
    valid_claim = erc20_settlement_ct.submit_claim(deposit=alice_and_bob_deposit)
    # Wait for the dispute period to end.
    erc20_settlement_ct.eth.block_number += multisig_settlement_ct.dispute_duration
    # Mallory attempts and fails to withdraw because there's another claim with priority
    try:
        multisig_settlement_ct.resolve_claim(invalid_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now alice and bob agree to send the money to a new on-chain multisig
    multisig_settlement_ct.resolve_claim(valid_claim, [alice.address, bob.address], 'on chain multisig address')
    # Check that the balances have updated
    assert erc20_ct.balanceOf('on chain multisig address') == 100
    assert erc20_ct.balanceOf(erc20_settlement_ct.address) == 0
