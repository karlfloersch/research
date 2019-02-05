from pytest import raises
from eth_tester.exceptions import TransactionFailed
from plasmalib.constants import CHALLENGE_PERIOD, PLASMA_BLOCK_INTERVAL


def test_compilation(pp):
    assert pp

