import rlp
from web3 import Web3
from plasmalib.operator.transactions import TransferRecord, get_null_tx, Signature, Transaction

def test_transactions():
    sender = Web3.sha3(1)[2:22]
    recipient = Web3.sha3(2)[2:22]
    transfer1 = TransferRecord(sender, recipient, 300, 300, 1, 250)
    transfer2 = TransferRecord(recipient, sender, 300, 300, 1, 250)
    sig1 = Signature(0, 0, 0)
    sig2 = Signature(0, 0, 0)
    tx = Transaction([transfer1.copy(), transfer2.copy()], [sig1.copy(), sig2.copy()])

    print(rlp.decode(rlp.encode(transfer1), TransferRecord))
    print(rlp.decode(rlp.encode(tx), Transaction))
    print('~~~~')
    print(rlp.encode(tx))
    print('~~~~')
    print(tx.hash)
    print(transfer1.hash)
    print('~~~~')
    null_tx = get_null_tx(300, 300, 250)
    print(rlp.decode(rlp.encode(null_tx), TransferRecord))
    print('~~~~')
    print(tx.transfers_hash)
