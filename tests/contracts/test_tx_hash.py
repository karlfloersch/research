from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


def addr_to_bytes(addr):
    return bytes.fromhex(addr[2:])

def test_addr_to_bytes(w3, tester, pp):
    addr = w3.eth.defaultAccount
    assert pp.addr_to_bytes(addr) == bytes.fromhex(addr[2:])

def test_tx_hash(w3, tester, pp):
    SENDER = addr_to_bytes(w3.eth.defaultAccount)
    RECIPIENT = addr_to_bytes(w3.eth.defaultAccount)
    START = 111323111
    OFFSET = 30

    expected_tx_hash = w3.sha3(
        SENDER +
        RECIPIENT +
        START.to_bytes(32, byteorder='big') +
        OFFSET.to_bytes(32, byteorder='big')
    )
    tx_hash = pp.tx_hash(
        w3.eth.defaultAccount,
        w3.eth.defaultAccount,
        START,
        OFFSET,
    )

    assert expected_tx_hash == tx_hash
