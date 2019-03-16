class OwnershipRevocationWitness:
    def __init__(self, next_state_commitment, signature, inclusion_witness):
        self.next_state_commitment = next_state_commitment
        self.signature = signature
        self.inclusion_witness = inclusion_witness

class OwnershipPredicate:
    dispute_duration = 10

    def __init__(self, parent_settlement_contract):
        self.parent = parent_settlement_contract

    def can_claim(self, claim, witness):
        # Anyone can submit a claim
        assert claim.commitment.state.recipient == witness
        return True

    def can_revoke(self, state_id, commitment, revocation_witness):
        # Check the state_id is in the commitment
        assert commitment.start <= state_id and commitment.end > state_id
        # Check the state_id is in the revocation_witness commitment
        assert revocation_witness.next_state_commitment.start <= state_id and revocation_witness.next_state_commitment.end > state_id
        # Check inclusion proof
        assert self.parent.commitment_chain.validate_commitment(revocation_witness.next_state_commitment,
                                                                self.parent.address,
                                                                revocation_witness.inclusion_witness)
        # Check that the previous owner signed off on the change
        assert commitment.state.recipient == revocation_witness.signature
        # Check that the spend is after the claim state
        assert commitment.plasma_block_number < revocation_witness.next_state_commitment.plasma_block_number
        return True

    def resolve_claim(self, tx_origin, claim, call_data=None):
        # Check that the resolution is called by the recipient
        assert tx_origin == claim.state.recipient
        # Transfer funds to the recipient
        self.parent.erc20_contract.transferFrom(self, claim.state.recipient, self.parent.deposits[claim.state.coin_id].value)

    def get_additional_lockup(self, state):
        return 0
