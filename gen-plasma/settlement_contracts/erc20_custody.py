from utils import State, Claim, ClaimQueue

class Erc20Deposit(State):
    def __init__(self, coin_id, plasma_block_number, value, new_settlement_contract, parameters):
        State.__init__(self, coin_id, plasma_block_number, new_settlement_contract, parameters)
        self.value = value

class Erc20SettlementContract:
    def __init__(self, eth, address, erc20_contract):
        self.eth = eth
        self.address = address
        self.erc20_contract = erc20_contract
        self.deposits = dict()
        self.total_deposits = 0
        self.commitments = []
        self.claim_queues = {}
        self.resolved_claims = []

    def deposit_ERC20(self, depositor, deposit_amount, new_settlement_contract, parameters):
        assert deposit_amount > 0
        # Make the transfer
        self.erc20_contract.transferFrom(depositor, self.address, deposit_amount)
        # Record the deposit
        plasma_block_number = len(self.commitments) - 1
        deposit = Erc20Deposit(self.total_deposits, plasma_block_number, deposit_amount, new_settlement_contract, parameters)
        self.deposits[deposit.coin_id] = deposit
        # Increment total deposits
        self.total_deposits += 1
        # Return deposit record
        return deposit

    def add_commitment(self, commit):
        self.commitments.append(commit)

    def validate_inclusion(self, state, inclusion_witness):
        # Check inclusion. Note we don't use an inclusion proof because our commitments include all data. Note this would often be a merkle proof
        assert state.plasma_block_number == inclusion_witness
        assert state in self.commitments[inclusion_witness]
        # Check that the state was added after the deposit of that coin
        assert self.deposits[state.coin_id] and self.deposits[state.coin_id].plasma_block_number < state.plasma_block_number
        return True

    def validate_deposit(self, state):
        # Check that the deposit was recorded
        assert state == self.deposits[state.coin_id]
        return True

    def submit_claim(self, state, inclusion_witness=None, child_claimability_witness=None):
        # Make sure we submitted either a committed or deposited state for this claim
        assert self.validate_inclusion(state, inclusion_witness) if inclusion_witness is not None else self.validate_deposit(state)
        # Create a claim for the state
        claim = Claim(self.eth.block_number, state)
        # Check that the child `can_claim` function returns true
        assert claim.state.new_settlement_contract.can_claim(claim, child_claimability_witness)
        # Create a new claim
        if claim.state.coin_id not in self.claim_queues:
            self.claim_queues[claim.state.coin_id] = ClaimQueue(claim)
        else:
            self.claim_queues[claim.state.coin_id].add(claim)
        return claim

    def dispute_claim(self, tx_origin, claim, transition_witness, new_state):
        # Call the settlement contract's `dispute_claim` function to ensure the claim should be deleted
        assert claim.state.new_settlement_contract.dispute_claim(tx_origin, claim.state, transition_witness, new_state)
        # Delete the claim
        claim_queue = self.claim_queues[claim.state.coin_id]
        claim_queue.remove(claim)

    def resolve_claim(self, tx_origin, claim, call_data=None):
        claim_queue = self.claim_queues[claim.state.coin_id]
        # Get the claim which is earliest in our claim queue
        recorded_claim = claim_queue.first()
        # Check that we are attempting to exit the earliest claim
        assert recorded_claim == claim
        # Check that the dispute_duration has passed
        assert self.eth.block_number >= claim.start_block_number + claim_queue.dispute_duration
        # Close the claim queue
        claim_queue.close()
        # Send the funds to the claim's settlement contract
        self.erc20_contract.transferFrom(self.address, claim.state.new_settlement_contract, self.deposits[claim.state.coin_id].value)
        # Call the settlement contract's `resolve_claim` function to ensure the claim should be resolved
        claim.state.new_settlement_contract.resolve_claim(tx_origin, claim, call_data)
