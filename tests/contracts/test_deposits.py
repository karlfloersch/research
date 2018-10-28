from pytest import raises
from eth_tester.exceptions import TransactionFailed
from plasmalib.constants import CHALLENGE_PERIOD, PLASMA_BLOCK_INTERVAL


def test_deposits(w3, tester, pp):
    DEPOSIT_VALUE = 555
    for account in w3.eth.accounts:
        pp.deposit(transact={'from': account, 'value': DEPOSIT_VALUE})
        assert pp.deposits(account) == DEPOSIT_VALUE
    assert pp.total_deposits() == DEPOSIT_VALUE * len(w3.eth.accounts)
