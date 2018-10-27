
CHALLENGE_PERIOD = 20
PLASMA_BLOCK_INTERVAL = 10
DEPOSIT_VALUE = 1039

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

def test_publish(plasmaprime, w3, tester):
    NEW_BLOCKS = 10
    for i in range(NEW_BLOCKS):
        # mine enough ethereum blocks to satisfy the minimum interval between plasma blocks
        tester.mine_blocks(num_blocks=PLASMA_BLOCK_INTERVAL)

        # publish some example hash
        h = w3.eth.getBlock('latest').hash
        bn = plasmaprime.functions.plasma_block_number().call()
        tx_hash = plasmaprime.functions.publish_hash(h).transact()
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        # check the correct hash was published
        assert h == plasmaprime.functions.hash_chain(bn).call()

        # confirm we can't immediately publish a new hash
        with pytest.raises(TransactionFailed):
            tx_hash = plasmaprime.functions.publish_hash(h).transact()

def test_exits(plasmaprime, w3, tester):
    w3.eth.defaultAccount = w3.eth.accounts[1]

    # deposit
    plasmaprime.functions.deposit().transact({'value': DEPOSIT_VALUE})

    # exit params
    PLASMA_BLOCK = 0
    START = 0
    OFFSET = 55

    # confirm we can't request exits for > total_deposit_value
    with pytest.raises(TransactionFailed):
        tx_hash = plasmaprime.functions.submit_exit(PLASMA_BLOCK, START, DEPOSIT_VALUE + 1).transact()

    # submit exit
    exit_id = plasmaprime.functions.submit_exit(PLASMA_BLOCK, START, OFFSET).call()
    tx_hash = plasmaprime.functions.submit_exit(PLASMA_BLOCK, START, OFFSET).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    # confirm on-chain exit data is correct
    assert plasmaprime.functions.exits__owner(exit_id).call() == w3.eth.defaultAccount
    assert plasmaprime.functions.exits__plasma_block(exit_id).call() == PLASMA_BLOCK
    assert plasmaprime.functions.exits__start(exit_id).call() == START
    assert plasmaprime.functions.exits__offset(exit_id).call() == OFFSET
    assert plasmaprime.functions.exits__challenge_count(exit_id).call() == 0
    assert plasmaprime.functions.exit_nonce().call() == exit_id + 1

    # try to finalize exit before challenge period is over
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    with pytest.raises(TransactionFailed):
        tx_hash = plasmaprime.functions.finalize_exit(exit_id).transact()
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert start_balance == end_balance

    # mine blocks until the challenge period is over
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)

    # confirm we can successfully exit now
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = plasmaprime.functions.finalize_exit(exit_id).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == OFFSET

    w3.eth.defaultAccount = w3.eth.accounts[0]

def test_challenges(plasmaprime, w3, tester, pp):
    w3.eth.defaultAccount = w3.eth.accounts[1]

    # exit params
    PLASMA_BLOCK = 0
    START = 0
    EXIT_VALUE = 55

    # deposit
    plasmaprime.functions.deposit().transact({'value': DEPOSIT_VALUE})

    # submit exit
    tx_hash = plasmaprime.functions.submit_exit(PLASMA_BLOCK, START, EXIT_VALUE).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    # challenge params
    EXIT_ID = 0
    TOKEN_ID = 5

    # confirm we can't challenge exits that don't exist yet
    with pytest.raises(TransactionFailed):
        tx_hash = plasmaprime.functions.challenge_completeness(1, 0).transact()

    # submit challenges
    CHALLENGE_COUNT = 10
    for i in range(CHALLENGE_COUNT):
        challenge_id = plasmaprime.functions.challenge_completeness(EXIT_ID, TOKEN_ID).call()
        tx_hash = plasmaprime.functions.challenge_completeness(EXIT_ID, TOKEN_ID).transact()
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        # confirm challenge is processed correctly
        assert plasmaprime.functions.challenges__exit_id(0).call() == EXIT_ID
        assert plasmaprime.functions.challenges__ongoing(0).call() == True
        assert plasmaprime.functions.challenges__token_id(0).call() == TOKEN_ID
        assert plasmaprime.functions.challenge_nonce().call() == challenge_id + 1
        assert plasmaprime.functions.exits__challenge_count(EXIT_ID).call() == i + 1

    # mine blocks until challenge period is over
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)

    # transaction info
    SENDER = w3.eth.defaultAccount
    RECIPIENT = w3.eth.defaultAccount
    START = 5
    OFFSET = 3
    proof = [w3.eth.getBlock('latest').hash for i in range(8)]

    # respond to challenges
    for i in range(CHALLENGE_COUNT):
        with pytest.raises(TransactionFailed):
            tx_hash = plasmaprime.functions.finalize_exit(EXIT_ID).transact()
        tx_hash = plasmaprime.functions.respond_completeness(
            i, # challenge ID
            SENDER,
            RECIPIENT,
            START,
            OFFSET,
            proof
            ).transact()
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        assert plasmaprime.functions.exits__challenge_count(EXIT_ID).call() == CHALLENGE_COUNT - i - 1

    # confirm we can successfully exit after responding to all challenges
    start_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    tx_hash = plasmaprime.functions.finalize_exit(EXIT_ID).transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    end_balance = w3.eth.getBalance(w3.eth.defaultAccount)
    assert end_balance - start_balance == EXIT_VALUE
