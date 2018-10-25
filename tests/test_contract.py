from web3 import Web3
from eth_tester import EthereumTester, PyEVMBackend
from vyper import compiler
from pprint import PrettyPrinter


tester = EthereumTester(backend=PyEVMBackend())
w3 = Web3(Web3.EthereumTesterProvider(tester))
w3.eth.setGasPriceStrategy(lambda web3, params: 0)
pp = PrettyPrinter(indent=4)

# path -> contract_factory
def factory(path):
    import os
    wd = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(wd, os.pardir, path)) as f:
        source = f.read()
    bytecode = '0x' + compiler.compile(source).hex()
    abi = compiler.mk_full_signature(source)
    return w3.eth.contract(abi=abi, bytecode=bytecode)

# contract_factory -> contract
def deploy(factory):
    tx_hash = factory.constructor().transact()
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    return w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=factory.abi,
    )

def test_deposits(factory):
    c = deploy(factory)
    for i in range(10):
        c.functions.deposit().transact({'value': i})
    total_deposits = c.functions.total_deposits().call()
    assert total_deposits == 45

f = factory('contracts/plasmaprime.v.py')
test_deposits(f)
