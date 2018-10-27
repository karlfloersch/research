from pytest import raises
from eth_tester.exceptions import TransactionFailed
from constants import *


def test_publication(w3, tester, pp):
    NEW_BLOCKS = 10
    for i in range(NEW_BLOCKS):
        # mine enough ethereum blocks to satisfy the minimum interval between plasma blocks
        tester.mine_blocks(num_blocks=PLASMA_BLOCK_INTERVAL)

        # publish some example hash
        h = w3.eth.getBlock('latest').hash
        bn = pp.functions.plasma_block_number().call()
        tx_hash = pp.functions.publish_hash(h).transact()
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

        # check the correct hash was published
        assert h == pp.functions.hash_chain(bn).call()

        # confirm we can't immediately publish a new hash
        with raises(TransactionFailed):
            tx_hash = pp.functions.publish_hash(h).transact()
