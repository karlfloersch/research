from pytest import raises
from eth_tester.exceptions import TransactionFailed
from eth_account import Account
from plasmalib.constants import CHALLENGE_PERIOD, PLASMA_BLOCK_INTERVAL
from plasmalib.utils import get_message_hash, addr_to_bytes, to_bytes32, get_tx_hash


def test_tx_hash(w3, tester, pp, acct):
    # plasma message info
    SENDER = w3.eth.defaultAccount
    RECIPIENT = w3.eth.defaultAccount
    START = 111323111
    OFFSET = 30

    # compute signature to be included in plasma tx
    message = (
        addr_to_bytes(SENDER) +
        addr_to_bytes(RECIPIENT) +
        to_bytes32(START) +
        to_bytes32(OFFSET)
    )
    message_hash = get_message_hash(SENDER, RECIPIENT, START, OFFSET)
    sig = acct.signHash(message_hash)

    # compute expected tx hash
    expected_tx_hash = get_tx_hash(SENDER, RECIPIENT, START, OFFSET, sig)

    # confirm tx hashes match
    tx_hash = pp.tx_hash(
        SENDER,
        RECIPIENT,
        START,
        OFFSET,
        sig.v,
        sig.r,
        sig.s,
    )
    assert tx_hash == expected_tx_hash
