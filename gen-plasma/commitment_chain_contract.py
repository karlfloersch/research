''' Commitment Block Structure
{
    subject_0: [commitment_0, commitment_1,...commitment_n],
    subject_1: [commitment_0, commitment_1,...commitment_n],
    ...
    subject_n: [commitment_0, commitment_1,...commitment_n]
}
'''

class CommitmentChainContract:
    def __init__(self, operator):
        self.operator = operator
        self.blocks = []

    def commit_block(self, msg_sender, block):
        assert msg_sender == self.operator
        self.blocks.append(block)

    def validate_commitment(self, commitment, subject, committment_witness):
        # Note that we are not providing merkle proofs and are instead faking it by storing the full blocks.
        block = self.blocks[commitment.block_number]
        # Make sure the subject contract address is in fact included in the block.
        # NOTE: We are mocking the inclusion & so we don't actually use the commitment witness.
        assert subject in block
        # Return whether or not this commitment was included
        return commitment in block[subject]
