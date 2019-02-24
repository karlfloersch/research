from settlement_contracts.transfer import TransferTransaction

def test_submit_claim_on_deposit(alice, erc20_settlement_ct, transfer_settlement_ct):
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})
    # Try submitting claim
    erc20_settlement_ct.submit_claim(deposit=alice_deposit)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues) == 1

def test_submit_claim_on_transaction(alice, bob, erc20_settlement_ct, transfer_settlement_ct):
    # Deposit and send a tx
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})  # Add deposit
    tx0_alice_to_bob = TransferTransaction(alice_deposit.coin_id, 0, alice.address, bob.address, transfer_settlement_ct, {})  # Create tx
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob])  # Add the tx to the first commitment
    # Try submitting claim
    erc20_settlement_ct.submit_claim(transaction=tx0_alice_to_bob)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues) == 1

def test_submit_dispute_on_deposit(alice, bob, erc20_settlement_ct, transfer_settlement_ct):
    # Deposit and send a tx
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})  # Add deposit
    tx0_alice_to_bob = TransferTransaction(alice_deposit.coin_id, 0, alice.address, bob.address, transfer_settlement_ct, {})  # Create tx
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob])  # Add the tx to the first commitment
    # Try submitting claim on deposit
    deposit_claim = erc20_settlement_ct.submit_claim(deposit=alice_deposit)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_to_bob.coin_id]) == 1
    # Now bob disputes claim in the transfer settlement contract with the spend
    erc20_settlement_ct.dispute_claim(bob.address, deposit_claim, tx0_alice_to_bob)
    # Check the claim was deleted
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_to_bob.coin_id]) == 0

def test_invalid_tx_exit_queue_resolution(alice, mallory, erc20_settlement_ct, transfer_settlement_ct, erc20_ct):
    # Deposit and send an invalid transaction
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})  # Add deposit
    tx0_mallory_to_mallory = TransferTransaction(alice_deposit.coin_id, 0, mallory.address, mallory.address, transfer_settlement_ct, {})  # Invalid tx
    erc20_settlement_ct.add_commitment([tx0_mallory_to_mallory])  # Add the tx to the first commitment
    # Submit a claim for the invalid transaction
    invalid_claim = erc20_settlement_ct.submit_claim(transaction=tx0_mallory_to_mallory)
    # Alice notices the invalid claim, and submits her own claim. Note that it is based on her deposit which is before the tx
    valid_claim = erc20_settlement_ct.submit_claim(deposit=alice_deposit)
    # Wait for the dispute period to end.
    erc20_settlement_ct.eth.block_number += transfer_settlement_ct.dispute_duration
    # Mallory attempts and fails to withdraw because there's another claim with priority
    try:
        erc20_settlement_ct.resolve_claim(mallory.address, invalid_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now alice withdraws
    erc20_settlement_ct.resolve_claim(alice.address, valid_claim)
    # Check that the balances have updated
    assert erc20_ct.balanceOf(alice.address) == 1000
    assert erc20_ct.balanceOf(erc20_settlement_ct.address) == 0
