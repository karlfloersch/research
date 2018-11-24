import rlp
from web3 import Web3
from plasmalib.operator.transactions import Transaction, Signature, MultiTx

def test_transactions():
    sender = Web3.sha3(1)[2:22]
    recipient = Web3.sha3(2)[2:22]
    tx1 = Transaction(sender, recipient, 300, 300, 1, 250)
    tx2 = Transaction(recipient, sender, 300, 300, 1, 250)
    sig1 = Signature(0, 0, 0)
    sig2 = Signature(0, 0, 0)
    multi_tx = MultiTx([tx1.copy(), tx2.copy()], [sig1.copy(), sig2.copy()])

    print(rlp.decode(rlp.encode(tx1), Transaction))
    print(rlp.decode(rlp.encode(multi_tx), MultiTx))
    print('~~~~')
    print(rlp.encode(multi_tx))
    print('~~~~')
    print(multi_tx.hash)
    print(tx1.hash)
