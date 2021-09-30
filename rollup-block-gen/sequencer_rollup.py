import pickle
from enum import Enum
from typing import List
from block_gen import Block

# A more complex rollup that allows for privilaged block
# production. This is achieved by allowing a "sequencer"
# to squeeze blocks into historical L1 blocks after the fact.

# This expands on the "simplest possible rollup" by, in addition
# to blocks being generated based on the first event, the sequencer
# may submit transactions in later blocks which contain many L2 blocks.

#################### Types ####################

# The sequencer timeout is the number of L1 blocks that the sequencer
# has to submit their blocks before they can no longer add sequencer
# blocks in between L1 blocks.
sequencer_timeout = 10 # AKA force inclusion period

# Batch Element Types
class BatchElementType(Enum):
    # Sequencer blocks are of type Block
    SEQUENCER_BLOCK = 1
    # L1 Block Numbers are of type L1BlockNumber
    L1_BLOCK_NUMBER = 2

class L1BlockNumber:
    block_number: int

class BatchElement:
    type: BatchElementType
    data: str

class SequencerBatch:
    elements: List[BatchElement]

#################### Functions ####################

# Generate the full rullup chain
def generate_rollup(l1_chain: List[Block]) -> List[Block]:
    # Simplest version of this is to repeatedly call
    # `generate_rollup_chain_subset` with block_n through block_n+sequencer_timeout
    pass

# Generate a subset of the rollup chain, used for fraud proofs.
# All blocks from `start_block` to `start_block+sequencer_timeout` must
# be supplied. This is how we can calculate both the deposit block and all the\
# sequencer blocks as well.
def generate_rollup_chain_subset(l1_chain_subset: List[Block]) -> List[Block]:
    # This will iterate through all blocks within this range and generate rollup blocks
    # which are found.
    pass