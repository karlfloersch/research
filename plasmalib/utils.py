
from web3 import Web3
from web3.contract import ConciseContract
from eth_tester import EthereumTester, PyEVMBackend
from vyper import compiler


class MST:
    h = None

    def __init__(self, l, r):
        self.h = Web3.sha3(l.h + r.h)

class Leaf:
    h = None
    data = None

    def __init__(self, data):
        self.h = Web3.sha3(data)

class Msg:
    def __init__(self, sender, recipient, start, offset):
        self.sender = sender
        self.recipient = recipient
        self.start = start
        self.offset = offset

    def get_hash(self):
        return Web3.sha3(
            addr_to_bytes(self.sender) +
            addr_to_bytes(self.recipient) +
            to_bytes32(self.start) +
            to_bytes32(self.offset)
        )

class Tx:
    def __init__(self, msg, signer):
        self.msg = msg
        self.sig = signer(msg.get_hash())

    def get_hash(self):
        return Web3.sha3(
            addr_to_bytes(self.msg.sender) +
            addr_to_bytes(self.msg.recipient) +
            to_bytes32(self.msg.start) +
            to_bytes32(self.msg.offset) +
            to_bytes32(self.sig.v) +
            to_bytes32(self.sig.r) +
            to_bytes32(self.sig.s)
        )

# class Sig:
    # def __init__(self, v, r, s):
        # self.v = v
        # self.r = r
        # self.s = s

def addr_to_bytes(addr):
    return bytes.fromhex(addr[2:])

def to_bytes32(i):
    return i.to_bytes(32, byteorder='big')

def contract_factory(w3, source):
    bytecode = '0x' + compiler.compile(source).hex()
    abi = compiler.mk_full_signature(source)
    return w3.eth.contract(abi=abi, bytecode=bytecode)
