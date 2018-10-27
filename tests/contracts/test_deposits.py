from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


def test_deposits(w3, tester, pp):
    DEPOSIT_VALUE = 555
    for account in w3.eth.accounts:
        tx_hash = pp.functions.deposit().transact({'from': account, 'value': DEPOSIT_VALUE})
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        assert pp.functions.deposits(account).call() == DEPOSIT_VALUE
    assert pp.functions.total_deposits().call() == DEPOSIT_VALUE * len(w3.eth.accounts)
