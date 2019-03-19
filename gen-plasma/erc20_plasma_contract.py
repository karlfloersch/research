from utils import State, Claim, Commitment, Challenge

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
        return Claim(commitment, eth_block_redeemable)

    def claim_deposit(self, deposit_end):
        deposit = self.claimable_ranges[deposit_end]
        claim = self._construct_claim(deposit)
        self.claims.append(claim)
        return len(self.claims) - 1

    def claim_commitment(self, commitment, commitment_witness, claimability_witness):
        assert self.commitment_chain.validate_commitment(commitment, self.address, commitment_witness)
        assert commitment.state.predicate.can_claim(commitment, claimability_witness)
        claim = self._construct_claim(commitment)
        self.claims.append(claim)
        return len(self.claims) - 1

    def revoke_claim(self, state_id, claim_id, revocation_witness):
        claim = self.claims[claim_id]
        # Call can revoke to check if the predicate allows this revocation attempt
        assert claim.commitment.state.predicate.can_revoke(state_id, claim.commitment, revocation_witness)
        # Delete the claim
        del self.claims[claim_id]

    def challenge_claim(self, earlier_claim_id, later_claim_id):
        earlier_claim = self.claims[earlier_claim_id]
        later_claim = self.claims[later_claim_id]
        # Make sure they overlap
        assert earlier_claim.commitment.start <= later_claim.commitment.end
        assert later_claim.commitment.start <= earlier_claim.commitment.end
        # Validate that the earlier claim is in fact earlier
        assert earlier_claim.commitment.plasma_block_number < later_claim.commitment.plasma_block_number
        # Make sure the later claim isn't already redeemable
        assert self.eth.block_number < later_claim.eth_block_redeemable
        # Create and record our new challenge
        new_challenge = Challenge(earlier_claim, later_claim)
        self.challenges.append(new_challenge)
        later_claim.num_challenges += 1
        # If the `eth_block_redeemable` of the earlier claim is longer than later claim, extend the later claim dispute period
        if later_claim.eth_block_redeemable < earlier_claim.eth_block_redeemable:
            later_claim.eth_block_redeemable = earlier_claim.eth_block_redeemable
        # Return our new challenge object
        return new_challenge

    def redeem_claim(self, claim_id, claimable_range_end):
        claim = self.claims[claim_id]
        # Check the claim's eth_block_redeemable has passed
        assert claim.eth_block_redeemable <= self.eth.block_number
        # Make sure that the claimable_range_end is actually in claimable_ranges
        assert claimable_range_end in self.claimable_ranges
        # Make sure the claim is within the claimable range
        assert claim.commitment.start >= self.claimable_ranges[claimable_range_end]
        assert claim.commitment.end <= claimable_range_end
        # Update claimable range
        if claim.commitment.start != self.claimable_ranges[claimable_range_end]:
            self.claimable_ranges[claim.commitment.start] = self.claimable_ranges[claimable_range_end]
        if claim.commitment.end != claimable_range_end:
            self.claimable_ranges[claimable_range_end] = claim.commitment.end
        # Approve coins for spending in predicate
        self.erc20_contract.approve(self.address, claim.commitment.state.predicate, claim.commitment.end - claim.commitment.start)
        # Finally redeem the claim
        claim.commitment.state.predicate.claim_redeemed(claim)

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
