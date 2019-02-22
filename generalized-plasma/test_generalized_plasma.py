from generalized_plasma import ERC20, User, Erc20SettlementContract, TransferSettlementContract, Erc20Deposit, CashTransaction, Eth
import pytest

# # User definitions
# alice = User('alice')
# bob = User('bob')
# # Ethereum object
# eth = {'block_number': 0}
# # Contract definitions
# omg = ERC20({alice.address: 1000, bob.address: 1000})
# omgSettlementCt = Erc20SettlementContract(eth, 'omgSettlement', omg)

alice = User('alice')
bob = User('bob')

@pytest.fixture
def erc20_ct():
    return ERC20({alice.address: 1000, bob.address: 1000})

@pytest.fixture
def erc20_settlement_ct(erc20_ct):
    eth = Eth(0)
    return Erc20SettlementContract(eth, 'erc20_settlement_ct', erc20_ct)

@pytest.fixture
def transfer_settlement_ct(erc20_settlement_ct):
    return TransferSettlementContract(erc20_settlement_ct)

# ~~~~ Erc20Contract tests ~~~~
def test_erc20_transfers(erc20_ct):
    assert erc20_ct.balanceOf(alice.address) == 1000 and erc20_ct.balanceOf(bob.address) == 1000
    erc20_ct.transferFrom(alice.address, bob.address, 500)
    assert erc20_ct.balanceOf(alice.address) == 500 and erc20_ct.balanceOf(bob.address) == 1500

# ~~~~ Erc20SettlementContract tests ~~~~
def test_deposit(erc20_ct, erc20_settlement_ct, transfer_settlement_ct):
    # Deposit some funds
    erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)
    # Assert the balances have changed
    assert erc20_ct.balanceOf(alice.address) == 900
    assert erc20_ct.balanceOf(erc20_settlement_ct.address) == 100
    # Assert that we recorded the deposit and incremented total_deposits
    assert len(erc20_settlement_ct.deposits) == 1 and isinstance(erc20_settlement_ct.deposits[0], Erc20Deposit)
    assert erc20_settlement_ct.total_deposits == 1

def test_commitments(erc20_settlement_ct, transfer_settlement_ct):
    # Deposit some funds
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)
    bob_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)
    # Create a tx which sends alice's coin to bob
    tx0_alice_to_bob = CashTransaction(alice_deposit.coin_id, alice.address, bob.address, 0, transfer_settlement_ct)
    tx1_bob_to_alice = CashTransaction(bob_deposit.coin_id, bob.address, alice.address, 0, transfer_settlement_ct)
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob, tx1_bob_to_alice])
    # Assert inclusion of our txs
    assert tx0_alice_to_bob in erc20_settlement_ct.commitments[0] and tx1_bob_to_alice in erc20_settlement_ct.commitments[0]

def test_submit_claim_on_deposit(erc20_settlement_ct, transfer_settlement_ct):
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)
    # Try submitting claim
    erc20_settlement_ct.submit_claim(deposit=alice_deposit)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues) == 1

def test_submit_claim_on_transaction(erc20_settlement_ct, transfer_settlement_ct):
    # Deposit and send a tx
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)  # Add deposit
    tx0_alice_to_bob = CashTransaction(alice_deposit.coin_id, alice.address, bob.address, 0, transfer_settlement_ct)  # Create tx
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob])  # Adding the tx to the first commitment
    # Try submitting claim
    erc20_settlement_ct.submit_claim(transaction=tx0_alice_to_bob)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues) == 1

def test_submit_dispute_on_deposit(erc20_settlement_ct, transfer_settlement_ct):
    # Deposit and send a tx
    alice_deposit = erc20_settlement_ct.deposit_ERC20(alice.address, 100, transfer_settlement_ct)  # Add deposit
    tx0_alice_to_bob = CashTransaction(alice_deposit.coin_id, alice.address, bob.address, 0, transfer_settlement_ct)  # Create tx
    erc20_settlement_ct.add_commitment([tx0_alice_to_bob])  # Adding the tx to the first commitment
    # Try submitting claim on deposit
    deposit_claim = erc20_settlement_ct.submit_claim(deposit=alice_deposit)
    # Check the claim was recorded
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_to_bob.coin_id]) == 1
    # Alice attempts to call dispute & fails
    try:
        assert not erc20_settlement_ct.dispute_claim(alice.address, deposit_claim)
    except Exception:
        pass
    # Now bob disputes claim in the transfer settlement contract
    transfer_settlement_ct.dispute_claim(deposit_claim, tx0_alice_to_bob)
    # Check the claim was deleted
    assert len(erc20_settlement_ct.claim_queues[tx0_alice_to_bob.coin_id]) == 0
