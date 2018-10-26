
EXIT_PERIOD = 20
DEPOSIT_VALUE = 1039
EXIT_VALUE = 157

from eth_tester.exceptions import TransactionFailed
import pytest

def test_compilation(plasmaprime):
    assert plasmaprime

def test_deposits(plasmaprime, w3):
    for account in w3.eth.accounts:
        tx_hash = plasmaprime.functions.deposit().transact({'from': account, 'value': DEPOSIT_VALUE})
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        assert plasmaprime.functions.deposits(account).call() == DEPOSIT_VALUE

    assert plasmaprime.functions.total_deposits().call() == DEPOSIT_VALUE * len(w3.eth.accounts)

def test_exits(plasmaprime, w3, tester):
    w3.eth.defaultAccount = w3.eth.accounts[1]

    # deposit
    plasmaprime.functions.deposit().transact({'value': DEPOSIT_VALUE})

    # exit params
    plasma_block = 0
    start = 0
    offset = EXIT_VALUE

    # submit exit
    exit_id = plasmaprime.functions.submit_exit(plasma_block, start, offset).call()
    tx_hash = plasmaprime.functions.submit_exit(plasma_block, start, offset).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    assert plasmaprime.functions.exits__owner(exit_id).call() == w3.eth.defaultAccount
    assert plasmaprime.functions.exits__plasma_block(exit_id).call() == plasma_block
    assert plasmaprime.functions.exits__start(exit_id).call() == start
    assert plasmaprime.functions.exits__offset(exit_id).call() == offset
    assert plasmaprime.functions.exit_nonce().call() == exit_id + 1

    # try to finalize exit before challenge period is over
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    with pytest.raises(TransactionFailed):
        tx_hash = plasmaprime.functions.finalize_exit(exit_id).transact()
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert start_balance == end_balance

    # mine blocks until the challenge period is over
    blocks = tester.mine_blocks(num_blocks=EXIT_PERIOD)

    # try again to finalize exit
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = plasmaprime.functions.finalize_exit(exit_id).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == offset
