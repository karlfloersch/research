class MultiSigTransitionWitness:
    def __init__(self, signatures, inclusion_witness):
        self.signatures = signatures  # Array of owner's signatures (in this it is just their names)
        self.inclusion_witness = inclusion_witness

class MultiSigPredicate:
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
        # Check that the all valid signatures are provided
        assert old_state.recipient == transition_witness.signatures
        # Check that the spend is after the claim state
        assert old_state.plasma_block_number < new_state.plasma_block_number
        return True

    def resolve_claim(self, tx_origin, claim, call_data):
        # Extract required information from call data
        recipients_sigs, destination = call_data
        # Check that the resolution is signed off on by all parties in the multisig
        assert recipients_sigs == claim.state.recipient
        # Transfer funds to the recipient
        self.parent.erc20_contract.transferFrom(self, destination, self.parent.deposits[claim.state.coin_id].value)
