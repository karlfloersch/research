import pytest

from web3 import Web3
from eth_tester import EthereumTester, PyEVMBackend
from vyper import compiler
import os

@pytest.fixture
def plasmaprime():
    tester = EthereumTester(backend=PyEVMBackend())
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    w3.eth.setGasPriceStrategy(lambda web3, params: 0)

    wd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(wd, os.pardir, 'contracts/plasmaprime.vy')) as f:
        source = f.read()
    bytecode = '0x' + compiler.compile(source).hex()
    abi = compiler.mk_full_signature(source)
    factory = w3.eth.contract(abi=abi, bytecode=bytecode)

    tx_hash = factory.constructor().transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=factory.abi,
    )
