from pytest import raises
from eth_tester.exceptions import TransactionFailed
from plasmalib.constants import *
from plasmalib.utils import *
from random import randrange


def test_responses(w3, tester, pp, accts):
    print("")
    # submit deposits
    for acct in accts:
        pp.deposit(transact={'from': acct.address, 'value': 1000})

    # create 2**8 random transactions
    TX_VALUE = 50
    txs = []
    for i in range(4):
        sender = accts[randrange(10)]
        recipient = accts[randrange(10)]
        msg = Msg(sender.address, recipient.address, TX_VALUE * i, TX_VALUE)
        txs.append(Tx(msg, sender.signHash))

    # publish plasma block
    tester.mine_blocks(num_blocks=PLASMA_BLOCK_INTERVAL)
    root = construct_tree(txs)
    pp.publish_hash(root.h, transact={})

    # params
    sender = txs[0].msg.sender
    recipient = txs[0].msg.recipient
    sig = txs[0].sig
    proof = [bytes(root.l.r.h), bytes(root.r.h)] + ([b'\x00'] * 6)

    # submit exit
    pp.submit_exit(0, 0, TX_VALUE, transact={'from': recipient})

    # submit challenge
    pp.challenge_completeness(0, 20, transact={})

    # confirm we can't exit while challenge is open
    tester.mine_blocks(num_blocks=CHALLENGE_PERIOD)
    with raises(TransactionFailed):
        pp.finalize_exit(0, transact={'from': recipient})

    # respond to challenge
    pp.respond_completeness(0, sender, recipient, 0, TX_VALUE, sig.v, sig.r, sig.s, proof, transact={'from': recipient})

    print(w3.eth.getBalance(recipient))
    pp.finalize_exit(0, transact={'from': recipient})
    print(w3.eth.getBalance(recipient))

