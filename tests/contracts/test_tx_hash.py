from pytest import raises
from eth_tester.exceptions import TransactionFailed
from eth_account import Account
from constants import *


def addr_to_bytes(addr):
    return bytes.fromhex(addr[2:])

def test_addr_to_bytes(w3, tester, pp):
    addr = w3.eth.defaultAccount
    assert pp.addr_to_bytes(addr) == bytes.fromhex(addr[2:])

def to_bytes32(i):
    return i.to_bytes(32, byteorder='big')


def test_tx_hash(w3, tester, pp):
    # create an account to work with
    acct = Account.create('some entropy')
    STARTING_VALUE = 1000
    w3.eth.sendTransaction({'to': acct.address, 'value': STARTING_VALUE})

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
    message_hash = w3.sha3(message)
    sig = acct.signHash(message_hash)

    # compute expected tx hash
    expected_tx_hash = w3.sha3(
        addr_to_bytes(SENDER) +
        addr_to_bytes(RECIPIENT) +
        to_bytes32(START) +
        to_bytes32(OFFSET) +
        to_bytes32(sig.v) +
        to_bytes32(sig.r) +
        to_bytes32(sig.s)
    )

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
