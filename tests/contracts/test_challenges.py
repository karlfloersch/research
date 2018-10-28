from pytest import raises
from eth_tester.exceptions import TransactionFailed
from plasmalib.constants import CHALLENGE_PERIOD, PLASMA_BLOCK_INTERVAL


def test_challenges(w3, tester, pp_live, acct):
    pp = pp_live

    # make a deposit
    DEPOSIT_VALUE = 333
    pp.deposit(transact={'value': DEPOSIT_VALUE})

    # submit an exit
    EXIT_START = 50
    EXIT_OFFSET = 34
    pp.submit_exit(0, EXIT_START, EXIT_OFFSET, transact={'from': acct.address})

    # submit a challenge
    CHALLENGE_TOKEN_INDEX = EXIT_START + 1
    pp.challenge_completeness(0, CHALLENGE_TOKEN_INDEX, transact={'from': acct.address})
    assert pp.challenge_nonce() == 1
    assert pp.challenges__exit_id(0) == 0
    assert pp.challenges__ongoing(0) == True
    assert pp.challenges__token_index(0) == CHALLENGE_TOKEN_INDEX

