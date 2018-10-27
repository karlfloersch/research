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
        bn = pp.plasma_block_number()
        tx_hash = pp.publish_hash(h, transact={})

        # check the correct hash was published
        assert h == pp.hash_chain(bn)

        # confirm we can't immediately publish a new hash
        with raises(TransactionFailed):
            tx_hash = pp.publish_hash(h, transact={})
