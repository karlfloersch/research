from web3 import Web3
from plasmalib.operator.transactions import (
    SimpleSerializableElement,
    SimpleSerializableList,
    TransferRecord,
    Signature,
)

def test_transactions():
    sender = Web3.sha3(1)[2:22]
    recipient = Web3.sha3(2)[2:22]
    tr1 = TransferRecord(sender, recipient, 0, 300, 300, 10, 0, 3)
    tr2 = TransferRecord(recipient, sender, 0, 100, 100, 10, 0, 3)
    sig1 = Signature(0, 1, 2)
    sig2 = Signature(3, 4, 5)
    tr1_encoding = tr1.encode()
    tr1_decoded = SimpleSerializableElement.decode(tr1_encoding, TransferRecord)
    # Verify that the decoded tx has the same hash
    assert tr1_decoded.hash == tr1.hash
    tr_list = SimpleSerializableList([tr1, tr2])
    sig_list = SimpleSerializableList([sig1, sig2])
    tr_list_encoding = tr_list.encode()
    sig_list_encoding = sig_list.encode()
    tr_decoded_list = SimpleSerializableList.decode(tr_list_encoding, TransferRecord)
    sig_decoded_list = SimpleSerializableList.decode(sig_list_encoding, Signature)
    # Verify that the hash & start pos seem to be correct
    assert tr_decoded_list[0].hash == tr1.hash
    assert tr_decoded_list[1].start == tr2.start
    assert sig_decoded_list[1].v == sig2.v
