from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


def test_exits(w3, tester, pp):
    DEPOSIT_VALUE = 555

    # deposit
    pp.functions.deposit().transact({'value': DEPOSIT_VALUE})

    # exit params
    PLASMA_BLOCK = 0
    START = 0
    OFFSET = 55

    # confirm we can't request exits for > total_deposit_value
    with raises(TransactionFailed):
        tx_hash = pp.functions.submit_exit(PLASMA_BLOCK, START, DEPOSIT_VALUE + 1).transact()

    # submit exit
    exit_id = pp.functions.submit_exit(PLASMA_BLOCK, START, OFFSET).call()
    tx_hash = pp.functions.submit_exit(PLASMA_BLOCK, START, OFFSET).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    # confirm on-chain exit data is correct
    assert pp.functions.exits__owner(exit_id).call() == w3.eth.defaultAccount
    assert pp.functions.exits__plasma_block(exit_id).call() == PLASMA_BLOCK
    assert pp.functions.exits__start(exit_id).call() == START
    assert pp.functions.exits__offset(exit_id).call() == OFFSET
    assert pp.functions.exits__challenge_count(exit_id).call() == 0
    assert pp.functions.exit_nonce().call() == exit_id + 1

    # try to finalize exit before challenge period is over
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    with raises(TransactionFailed):
        tx_hash = pp.functions.finalize_exit(exit_id).transact()
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert start_balance == end_balance

    # mine blocks until the challenge period is over
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)

    # confirm we can successfully exit now
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = pp.functions.finalize_exit(exit_id).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == OFFSET
