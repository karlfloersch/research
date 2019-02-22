import pytest
from generalized_plasma import ERC20, User, Erc20SettlementContract, Eth
from settlement_contracts.transfer import TransferSettlementContract

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
def erc20_settlement_ct(eth, erc20_ct):
    eth = Eth(0)
    return Erc20SettlementContract(eth, 'erc20_settlement_ct', erc20_ct)

@pytest.fixture
def transfer_settlement_ct(erc20_settlement_ct):
    return TransferSettlementContract(erc20_settlement_ct)
