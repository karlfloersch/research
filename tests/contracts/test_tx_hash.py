from pytest import raises
from eth_tester.exceptions import TransactionFailed
from eth_account import Account
from constants import *


def addr_to_bytes(addr):
    return bytes.fromhex(addr[2:])

def test_addr_to_bytes(w3, tester, pp):
    addr = w3.eth.defaultAccount
    assert pp.addr_to_bytes(addr) == bytes.fromhex(addr[2:])

def test_tx_hash(w3, tester, pp):
    # create an account to work with
    acct = Account.create('some entropy')
    STARTING_VALUE = 1000
    w3.eth.sendTransaction({'to': acct.address, 'value': STARTING_VALUE})

    # plasma tx info
    SENDER = w3.eth.defaultAccount
    RECIPIENT = w3.eth.defaultAccount
    START = 111323111
    OFFSET = 30

    # compute signature to be included in plasma tx
    message = (
        addr_to_bytes(SENDER) +
        addr_to_bytes(RECIPIENT) +
        START.to_bytes(32, byteorder='big') +
        OFFSET.to_bytes(32, byteorder='big')
    )
    message_hash = w3.sha3(message)
    signature = acct.signHash(message_hash).signature

    # confirm tx_hash is computed correctly
    expected_tx_hash = w3.sha3(message + bytes(signature))
    tx_hash = pp.tx_hash(
        SENDER,
        RECIPIENT,
        START,
        OFFSET,
        bytes(signature),
    )
    assert tx_hash == expected_tx_hash
