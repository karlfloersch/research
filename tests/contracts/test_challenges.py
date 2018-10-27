from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


# exit params
PLASMA_BLOCK = 0
EXIT_START_INDEX = 0
EXIT_VALUE = 55

# challenge params
EXIT_ID = 0
TOKEN_INDEX = 5


def test_challenges(w3, tester, pp):
    # deposit
    tx_hash = pp.deposit(transact={'value': EXIT_VALUE})

    # publish a plasma block
    tester.mine_blocks(num_blocks=PLASMA_BLOCK_INTERVAL)
    h = w3.eth.getBlock('latest').hash
    tx_hash = pp.publish_hash(h, transact={})

    # submit exit
    tx_hash = pp.submit_exit(PLASMA_BLOCK, EXIT_START_INDEX, EXIT_VALUE, transact={})

    # confirm we can't challenge exits that don't exist yet
    with raises(TransactionFailed):
        tx_hash = pp.challenge_completeness(EXIT_ID + 1, 0, transact={})

    # submit challenges
    CHALLENGE_COUNT = 10
    for i in range(CHALLENGE_COUNT):
        challenge_id = pp.challenge_completeness(EXIT_ID, TOKEN_INDEX)
        tx_hash = pp.challenge_completeness(EXIT_ID, TOKEN_INDEX, transact={})

        # confirm challenge is processed correctly
        assert pp.challenges__exit_id(0) == EXIT_ID
        assert pp.challenges__ongoing(0) == True
        assert pp.challenges__token_id(0) == TOKEN_INDEX
        assert pp.challenge_nonce() == challenge_id + 1
        assert pp.exits__challenge_count(EXIT_ID) == i + 1

    # mine blocks until challenge period is over
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)

    # transaction info
    SENDER = w3.eth.defaultAccount
    RECIPIENT = w3.eth.defaultAccount
    TRANSACTION_START_INDEX = 5
    TRANSACTION_VALUE = 3
    proof = [w3.eth.getBlock('latest').hash for i in range(8)]

    # respond to challenges
    for i in range(CHALLENGE_COUNT):
        with raises(TransactionFailed):
            tx_hash = pp.finalize_exit(EXIT_ID, transact={})
        tx_hash = pp.respond_completeness(
            i, # challenge ID
            SENDER,
            RECIPIENT,
            TRANSACTION_START_INDEX,
            TRANSACTION_VALUE,
            proof,
            transact={},
            )
        assert pp.exits__challenge_count(EXIT_ID) == CHALLENGE_COUNT - i - 1

    # confirm we can successfully exit after responding to all challenges
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = pp.finalize_exit(EXIT_ID, transact={})
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == EXIT_VALUE
