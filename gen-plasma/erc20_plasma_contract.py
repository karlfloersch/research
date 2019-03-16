from utils import State, Claim, Commitment

class ClaimableRange:
    def __init__(self, start, is_set):
        self.start = start

class Erc20PlasmaContract:
    def __init__(self, eth, address, erc20_contract, commitment_chain, DISPUTE_PERIOD):
        # Settings
        self.eth = eth
        self.address = address
        self.erc20_contract = erc20_contract
        self.commitment_chain = commitment_chain
        self.DISPUTE_PERIOD = DISPUTE_PERIOD
        # Datastructures
        self.total_deposits = 0
        self.claimable_ranges = dict()
        self.claims = []
        self.challenges = []

    def deposit(self, depositor, deposit_amount, predicate, parameters):
        assert deposit_amount > 0
        # Make the transfer
        self.erc20_contract.transferFrom(depositor, self.address, deposit_amount)
        # Record the deposit first by collecting the preceeding plasma block number
        preceding_plasma_block_number = len(self.commitment_chain.blocks) - 1
        # Next compute the start and end positions of the deposit
        deposit_start = self.total_deposits
        deposit_end = self.total_deposits + deposit_amount
        # Create the initial state which we will record to in this deposit
        initial_state = State(predicate, parameters)
        # Create the depoisit object
        deposit = Commitment(initial_state, deposit_start, deposit_end, preceding_plasma_block_number)
        # And store the deposit in our mapping of ranges which can be claimed
        self.claimable_ranges[deposit_end] = deposit
        # Increment total deposits
        self.total_deposits += deposit_amount
        # Return deposit record
        return deposit

    def _construct_claim(self, commitment):
        additional_lockup_duration = commitment.state.predicate.get_additional_lockup(commitment.state)
        eth_block_redeemable = self.eth.block_number + self.DISPUTE_PERIOD + additional_lockup_duration
        return Claim(commitment, eth_block_redeemable, 0)

    def claim_deposit(self, deposit_end):
        deposit = self.claimable_ranges[deposit_end]
        claim = self._construct_claim(deposit)
        self.claims.append(claim)
        return len(self.claims) - 1

    def claim_commitment(self, commitment, commitment_witness, claimability_witness):
        assert self.commitment_chain.validate_commitment(commitment, self.address, commitment_witness)
        assert commitment.state.predicate.can_claim(commitment, commitment_witness)
        claim = self._construct_claim(commitment)
        self.claims.append(claim)
        return len(self.claims) - 1

    def revoke_claim(self, state_id, claim_id, revocation_witness):
        claim = self.claims[claim_id]
        # Call can revoke to check if the predicate allows this revocation attempt
        assert claim.commitment.state.predicate.can_revoke(state_id, claim.commitment, revocation_witness)
        # Delete the claim
        del self.claims[claim_id]

    # def dispute_claim(self, tx_origin, claim, transition_witness, new_state):
    #     # Call the settlement contract's `dispute_claim` function to ensure the claim should be deleted
    #     assert claim.state.predicate.dispute_claim(tx_origin, claim.state, transition_witness, new_state)
    #     # Delete the claim
    #     claim_queue = self.claim_queues[claim.state.coin_id]
    #     claim_queue.remove(claim)

    # def resolve_claim(self, tx_origin, claim, call_data=None):
    #     claim_queue = self.claim_queues[claim.state.coin_id]
    #     # Get the claim which is earliest in our claim queue
    #     recorded_claim = claim_queue.first()
    #     # Check that we are attempting to exit the earliest claim
    #     assert recorded_claim == claim
    #     # Check that the dispute_duration has passed
    #     assert self.eth.block_number >= claim.start_block_number + claim_queue.dispute_duration
    #     # Close the claim queue
    #     claim_queue.close()
    #     # Send the funds to the claim's settlement contract
    #     self.erc20_contract.transferFrom(self.address, claim.state.predicate, self.deposits[claim.state.coin_id].value)
    #     # Call the settlement contract's `resolve_claim` function to ensure the claim should be resolved
    #     claim.state.predicate.resolve_claim(tx_origin, claim, call_data)
