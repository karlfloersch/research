import pytest
import os

from web3 import Web3
from web3.contract import ConciseContract
from eth_tester import EthereumTester, PyEVMBackend
from vyper import compiler
from plasmalib.utils import contract_factory


@pytest.fixture(scope="session")
def tester():
    return EthereumTester(backend=PyEVMBackend())

@pytest.fixture(scope="session")
def w3(tester):
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    w3.eth.setGasPriceStrategy(lambda web3, params: 0)
    w3.eth.defaultAccount = w3.eth.accounts[0]
    return w3

@pytest.fixture
def pp(w3):
    wd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(wd, os.pardir, 'contracts/plasmaprime.vy')) as f:
        source = f.read()
    factory = contract_factory(w3, source)
    tx_hash = factory.constructor().transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return ConciseContract(w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=factory.abi,
    ))
