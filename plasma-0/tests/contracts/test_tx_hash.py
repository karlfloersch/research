from pytest import raises
from eth_tester.exceptions import TransactionFailed
from eth_account import Account
from plasmalib.constants import CHALLENGE_PERIOD, PLASMA_BLOCK_INTERVAL
from plasmalib.utils import *


def test_tx_hash(w3, tester, pp, acct):
    # plasma message info
    SENDER = w3.eth.defaultAccount
    RECIPIENT = w3.eth.defaultAccount
    START = 111323111
    OFFSET = 30

    # compute signature to be included in plasma tx
    msg = Msg(SENDER, RECIPIENT, START, OFFSET)
    message_hash = msg.h

    # compute expected tx hash
    tx = Tx(msg, acct.signHash)
    expected_tx_hash = tx.h

    # confirm tx hashes match
    tx_hash = pp.tx_hash(
        SENDER,
        RECIPIENT,
        START,
        OFFSET,
        tx.sigv,
        tx.sigr,
        tx.sigs,
    )
    assert tx_hash == expected_tx_hash
