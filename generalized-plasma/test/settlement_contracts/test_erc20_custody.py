from settlement_contracts.erc20_custody import Erc20Deposit
from settlement_contracts.transfer import TransferTransaction

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
    tx0_alice_to_bob = TransferTransaction(alice_deposit.coin_id, 0, alice.address, transfer_settlement_ct, {'recipient': bob.address})
    tx1_bob_to_alice = TransferTransaction(bob_deposit.coin_id, 0, bob.address, transfer_settlement_ct, {'recipient': alice.address})
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob, tx1_bob_to_alice])
    # Assert inclusion of our txs
    assert tx0_alice_to_bob in erc20_settlement_ct.commitments[0] and tx1_bob_to_alice in erc20_settlement_ct.commitments[0]
