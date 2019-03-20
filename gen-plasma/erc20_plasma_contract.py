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
        self.claims[claim_id].is_revoked = True

    def remove_challenge(self, challenge_id):
        challenge = self.challenges[challenge_id]
        earlier_claim = self.claims[challenge.earlier_claim_id]
        assert earlier_claim.is_revoked
        # All checks have passed, we have an earlier claim that was revoked and the challenge is no longer valid.
        # Decrement the challenge count on the later claim
        self.claims[challenge.later_claim_id].num_challenges -= 1
        # Delete the challenge
        del self.challenges[challenge_id]

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
        new_challenge = Challenge(earlier_claim_id, later_claim_id)
        self.challenges.append(new_challenge)
        later_claim.num_challenges += 1
        # If the `eth_block_redeemable` of the earlier claim is longer than later claim, extend the later claim dispute period
        if later_claim.eth_block_redeemable < earlier_claim.eth_block_redeemable:
            later_claim.eth_block_redeemable = earlier_claim.eth_block_redeemable
        # Return our new challenge object
        return len(self.challenges) - 1

    def redeem_claim(self, claim_id, claimable_range_end):
        claim = self.claims[claim_id]
        # Check the claim's eth_block_redeemable has passed
        assert claim.eth_block_redeemable <= self.eth.block_number
        # Check that there are no open challenges for the claim
        assert claim.num_challenges == 0
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
