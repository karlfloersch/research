from generalized_plasma import Erc20Deposit
from settlement_contracts.transfer import TransferTransaction

# ~~~~ Erc20Contract tests ~~~~
def test_erc20_transfers(alice, bob, erc20_ct):
    assert erc20_ct.balanceOf(alice.address) == 1000 and erc20_ct.balanceOf(bob.address) == 1000
    erc20_ct.transferFrom(alice.address, bob.address, 500)
    assert erc20_ct.balanceOf(alice.address) == 500 and erc20_ct.balanceOf(bob.address) == 1500

# ~~~~ Erc20SettlementContract tests ~~~~
def test_deposit(alice, erc20_ct, erc20_settlement_ct, transfer_settlement_ct):
    # Deposit some funds
    erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})
    # Assert the balances have changed
    assert erc20_ct.balanceOf(alice.address) == 900
    assert erc20_ct.balanceOf(erc20_settlement_ct.address) == 100
    # Assert that we recorded the deposit and incremented total_deposits
    assert len(erc20_settlement_ct.deposits) == 1 and isinstance(erc20_settlement_ct.deposits[0], Erc20Deposit)
    assert erc20_settlement_ct.total_deposits == 1

def test_commitments(alice, bob, erc20_settlement_ct, transfer_settlement_ct):
    # Deposit some funds
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': alice.address})
    bob_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct, {'recipient': bob.address})
    # Create a tx which sends alice's coin to bob
    tx0_alice_to_bob = TransferTransaction(alice_deposit.coin_id, 0, alice.address, bob.address, transfer_settlement_ct, {})
    tx1_bob_to_alice = TransferTransaction(bob_deposit.coin_id, 0, bob.address, alice.address, transfer_settlement_ct, {})
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob, tx1_bob_to_alice])
    # Assert inclusion of our txs
    assert tx0_alice_to_bob in erc20_settlement_ct.commitments[0] and tx1_bob_to_alice in erc20_settlement_ct.commitments[0]

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
    # Alice attempts to call dispute directly & fails (can only be called by settlement contract
    try:
        erc20_settlement_ct.dispute_claim(alice.address, deposit_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now bob disputes claim in the transfer settlement contract with the spend
    transfer_settlement_ct.dispute_claim(deposit_claim, tx0_alice_to_bob)
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
        transfer_settlement_ct.resolve_claim(invalid_claim)
        throws = False
    except Exception:
        throws = True
    assert throws
    # Now alice withdraws
    transfer_settlement_ct.resolve_claim(valid_claim)
    # Check that the balances have updated
    assert erc20_ct.balanceOf(alice.address) == 1000
    assert erc20_ct.balanceOf(erc20_settlement_ct.address) == 0
