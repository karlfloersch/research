# from utils import State, Claim
from utils import State

class Erc20Deposit:
    def __init__(self, state, start, end, preceding_plasma_block_number):
        self.state = state
        self.start = start
        self.end = end
        self.preceding_plasma_block_number = preceding_plasma_block_number

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
        deposit = Erc20Deposit(initial_state, deposit_start, deposit_end, preceding_plasma_block_number)
        # And store the deposit in our mapping of ranges which can be claimed
        self.claimable_ranges[deposit_end] = deposit
        # Increment total deposits
        self.total_deposits += deposit_amount
        # Return deposit record
        return deposit

    # def validate_inclusion(self, state, inclusion_witness):
    #     # Check inclusion. Note we don't use an inclusion proof because our commitments include all data. Note this would often be a merkle proof
    #     assert state.plasma_block_number == inclusion_witness
    #     assert state in self.commitments[inclusion_witness]
    #     # Check that the state was added after the deposit of that coin
    #     assert self.deposits[state.coin_id] and self.deposits[state.coin_id].plasma_block_number < state.plasma_block_number
    #     return True

    # def validate_deposit(self, state):
    #     # Check that the deposit was recorded
    #     assert state == self.deposits[state.coin_id]
    #     return True

    # # TODO: Break this out into two functions, `claimCommittment` and `claimDeposit`
    # def submit_claim(self, state, inclusion_witness=None, child_claimability_witness=None):
    #     # Make sure we submitted either a committed or deposited state for this claim
    #     assert self.validate_inclusion(state, inclusion_witness) if inclusion_witness is not None else self.validate_deposit(state)
    #     # Create a claim for the state
    #     claim = Claim(self.eth.block_number, state)
    #     # Check that the child `can_claim` function returns true
    #     assert claim.state.predicate.can_claim(claim, child_claimability_witness)
    #     # Create a new claim
    #     self.claims.append(claim)
    #     return claim

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
