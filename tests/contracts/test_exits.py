from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


def test_exits(w3, tester, pp):
    DEPOSIT_VALUE = 555

    # deposit
    pp.deposit(transact={'value': DEPOSIT_VALUE})

    # exit params
    PLASMA_BLOCK = 0
    START = 0
    OFFSET = 55

    # confirm we can't request exits for > total_deposit_value
    with raises(TransactionFailed):
        tx_hash = pp.submit_exit(PLASMA_BLOCK, START, DEPOSIT_VALUE + 1, transact={})

    # submit exit
    exit_id = pp.submit_exit(PLASMA_BLOCK, START, OFFSET)
    tx_hash = pp.submit_exit(PLASMA_BLOCK, START, OFFSET, transact={})

    # confirm on-chain exit data is correct
    assert pp.exits__owner(exit_id) == w3.eth.defaultAccount
    assert pp.exits__plasma_block(exit_id) == PLASMA_BLOCK
    assert pp.exits__start(exit_id) == START
    assert pp.exits__offset(exit_id) == OFFSET
    assert pp.exits__challenge_count(exit_id) == 0
    assert pp.exit_nonce() == exit_id + 1

    # try to finalize exit before challenge period is over
    with raises(TransactionFailed):
        tx_hash = pp.finalize_exit(exit_id, transact={})

    # mine blocks until the challenge period is over
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)

    # confirm we can successfully exit now
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = pp.finalize_exit(exit_id, transact={})
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == OFFSET
