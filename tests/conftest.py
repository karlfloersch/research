import pytest
import os

from web3 import Web3
from web3.contract import ConciseContract
from eth_tester import EthereumTester, PyEVMBackend
from eth_account import Account
from plasmalib.utils import contract_factory
from plasmalib.constants import PLASMA_BLOCK_INTERVAL
from random import randrange, seed


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
def acct(w3):
    seed()
    STARTING_VALUE = Web3.toWei(100, 'ether')
    PASSPHRASE = 'not a real passphrase'
    acct = Account.create(randrange(10**32))
    w3.eth.sendTransaction({'to': acct.address, 'value': STARTING_VALUE})
    w3.personal.importRawKey(acct.privateKey, PASSPHRASE)
    w3.personal.unlockAccount(acct.address, PASSPHRASE)
    return acct

@pytest.fixture
def accts(w3):
    seed()
    STARTING_VALUE = Web3.toWei(100, 'ether')
    PASSPHRASE = 'not a real passphrase'
    accts = [Account.create(randrange(10**32)) for i in range(10)]
    for i in range(10):
        w3.eth.sendTransaction({'to': accts[i].address, 'value': STARTING_VALUE})
        w3.personal.importRawKey(accts[i].privateKey, PASSPHRASE)
        w3.personal.unlockAccount(accts[i].address, PASSPHRASE)
    return accts

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

@pytest.fixture
def pp_live(w3, tester, pp):
    ITERATION = 10

    # submit some garbage plasma blocks
    h = b'\x8b' * 32
    for i in range(10):
        tester.mine_blocks(num_blocks=PLASMA_BLOCK_INTERVAL)
        pp.publish_hash(h, transact={})
    return pp
