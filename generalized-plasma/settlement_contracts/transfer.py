class TransferTransitionWitness:
    def __init__(self, signature, inclusion_witness):
        self.signature = signature
        self.inclusion_witness = inclusion_witness

class TransferSettlementContract:
    dispute_duration = 10

    def __init__(self, parent_settlement_contract):
        self.parent = parent_settlement_contract

    def can_claim(self, claim, witness):
        # Anyone can submit a claim
        return True

    def dispute_claim(self, tx_origin, old_state, transition_witness, new_state):
        # Check these are spends of the same coin
        assert old_state.coin_id == new_state.coin_id
        # Check inclusion proof
        assert self.parent.validate_inclusion(new_state, transition_witness.inclusion_witness)
        # Check that the signature is valid
        assert old_state.recipient == transition_witness.signature
        # Check that the spend is after the claim state
        assert old_state.plasma_block_number < new_state.plasma_block_number
        return True

    def resolve_claim(self, tx_origin, claim, call_data=None):
        # Check that the resolution is called by the recipient
        assert tx_origin == claim.state.recipient
        # Transfer funds to the recipient
        self.parent.erc20_contract.transferFrom(self, claim.state.recipient, self.parent.deposits[claim.state.coin_id].value)
