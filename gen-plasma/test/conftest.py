import pytest
from utils import ERC20, User, Eth
from erc20_plasma_contract import Erc20PlasmaContract
from predicates.ownership import OwnershipPredicate
from commitment_chain_contract import CommitmentChainContract

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
def erc20_ct(alice, bob, mallory):
    return ERC20({alice.address: 1000, bob.address: 1000, mallory.address: 1000})

@pytest.fixture
def eth():
    return Eth(0)

@pytest.fixture
def operator():
    return User('Operator')

@pytest.fixture
def erc20_plasma_ct(eth, operator, erc20_ct):
    eth = Eth(0)
    commitment_chain_contract = CommitmentChainContract(operator.address)
    return Erc20PlasmaContract(eth, 'erc20_plasma_ct', erc20_ct, commitment_chain_contract, 10)

@pytest.fixture
def ownership_predicate(erc20_plasma_ct):
    return OwnershipPredicate(erc20_plasma_ct)
