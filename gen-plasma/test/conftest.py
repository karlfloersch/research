import pytest
from utils import ERC20, User, Eth
from erc20_plasma_contract import Erc20PlasmaContract
from predicates.transfer import TransferPredicate

@pytest.fixture
def alice():
    return User('alice')

@pytest.fixture
def bob():
    return User('bob')

@pytest.fixture
def charlie():
    return User('charlie')

@pytest.fixture
def mallory():
    return User('mallory')

@pytest.fixture
def erc20_ct(alice, bob):
    return ERC20({alice.address: 1000, bob.address: 1000})

@pytest.fixture
def eth():
    return Eth(0)

@pytest.fixture
def erc20_plasma_ct(eth, erc20_ct):
    eth = Eth(0)
    return Erc20PlasmaContract(eth, 'erc20_plasma_ct', erc20_ct)

@pytest.fixture
def transfer_predicate(erc20_plasma_ct):
    return TransferPredicate(erc20_plasma_ct)
