
from web3 import Web3
from web3.contract import ConciseContract
from eth_tester import EthereumTester, PyEVMBackend
from vyper import compiler

def addr_to_bytes(addr):
    return bytes.fromhex(addr[2:])

def to_bytes32(i):
    return i.to_bytes(32, byteorder='big')

def get_message_hash(
        sender, # address as string beginning with 0x
        recipient, # address as string beginning with 0x
        start, # int
        offset, # int
):
    message = (
        addr_to_bytes(sender) +
        addr_to_bytes(recipient) +
        to_bytes32(start) +
        to_bytes32(offset)
    )
    return Web3.sha3(message)

def get_tx_hash(
        sender,
        recipient,
        start,
        offset,
        sig, # must contain sig.v, sig.r, sig.s
):
    return Web3.sha3(
        addr_to_bytes(sender) +
        addr_to_bytes(recipient) +
        to_bytes32(start) +
        to_bytes32(offset) +
        to_bytes32(sig.v) +
        to_bytes32(sig.r) +
        to_bytes32(sig.s)
    )

def contract_factory(w3, source):
    bytecode = '0x' + compiler.compile(source).hex()
    abi = compiler.mk_full_signature(source)
    return w3.eth.contract(abi=abi, bytecode=bytecode)
