import copy
import pickle
from block_gen import Block, Event, gen_dummy_block
from typing import List
from sequencer_rollup import (
    generate_rollup,
    sequencer_timeout,
    SequencerBatch,
    BatchElement,
    BatchElementType,
    L1BlockNumber
)

def test_generate_rollup():
    l1_chain: List[Block] = []

    for i in range(100):
        block = gen_dummy_block(i)
        encoded_l2_deposit = pickle.dumps(block)
        block["events"][0]["data"] = encoded_l2_deposit
        # Add sequencer batches
        if i > sequencer_timeout:
            batch_elements: BatchElement = []
            if i % 2 != 0:
                be = gen_l1_block_batch_element(i, sequencer_timeout)
                batch_elements.append(be)
            seq_be = gen_sequencer_block_batch_element(l1_chain[i - sequencer_timeout])
            batch_elements.append(seq_be)
            # Now that we have the batch elements, let's encode and add it as a tx!
            encoded_batch_elements = pickle.dumps(batch_elements)
            block["txs"][0]["data"] = encoded_batch_elements


        l1_chain.append(block)

    print("Generated the L1 chain successfully!")
    # l2_chain = generate_rollup(l1_chain)

def gen_l1_block_batch_element(i: int, seq_timeout: int) -> BatchElement:
    int_l1_block_num: int = i - seq_timeout
    l1_block_num: L1BlockNumber = {
        "block_number": int_l1_block_num
    }
    encoded_l1_block_num = pickle.dumps(l1_block_num)
    be: BatchElement = {
        "type": BatchElementType.L1_BLOCK_NUMBER,
        "data": encoded_l1_block_num
    }
    return be

def gen_sequencer_block_batch_element(seq_block: Block) -> BatchElement:
    encoded_sequencer_block = pickle.dumps(seq_block)
    be: BatchElement = {
        "type": BatchElementType.L1_BLOCK_NUMBER,
        "data": encoded_sequencer_block
    }
    return be