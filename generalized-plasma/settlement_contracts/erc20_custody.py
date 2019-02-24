from utils import Transaction, Claim, ClaimQueue

class Erc20Deposit(Transaction):
    def __init__(self, coin_id, plasma_block_number, value, settlement_contract, parameters):
        Transaction.__init__(self, coin_id, plasma_block_number, settlement_contract, parameters)
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

    def deposit_ERC20(self, depositor, deposit_amount, settlement_contract, parameters):
        assert deposit_amount > 0
        # Make the transfer
        self.erc20_contract.transferFrom(depositor, self.address, deposit_amount)
        # Record the deposit
        plasma_block_number = len(self.commitments) - 1
        deposit = Erc20Deposit(self.total_deposits, plasma_block_number, deposit_amount, settlement_contract, parameters)
        self.deposits[deposit.coin_id] = deposit
        # Increment total deposits
        self.total_deposits += 1
        # Return deposit record
        return deposit

    def add_commitment(self, commit):
        self.commitments.append(commit)

    def _validate_transaction(self, transaction, inclusion_witness):
        if transaction is None:
            return False
        # Check inclusion. Note we don't need the inclusion_witness because we don't use an accumulator
        assert transaction in self.commitments[transaction.plasma_block_number]
        # Check that the transaction was added after the deposit of that coin
        assert self.deposits[transaction.coin_id] and self.deposits[transaction.coin_id].plasma_block_number < transaction.plasma_block_number
        return True

    def _validate_deposit(self, deposit):
        if deposit is None:
            return False
        # Check that the deposit was recorded
        assert deposit == self.deposits[deposit.coin_id]
        return True

    def submit_claim(self, transaction=None, deposit=None, inclusion_witness=None, claim_witness=None):
        # Make sure we submitted either a valid transaction or deposit for this claim (no erc20 claims can be on coins that don't exist)
        assert self._validate_transaction(transaction, inclusion_witness) or self._validate_deposit(deposit)
        # Create a claim for either the transaction or deposit
        claim = Claim(self.eth.block_number, transaction) if transaction is not None else Claim(self.eth.block_number, deposit)
        # Check that the child submit claim function returns true
        assert claim.transaction.settlement_contract.submit_claim(claim, claim_witness)
        # Create a new claim
        if claim.transaction.coin_id not in self.claim_queues:
            self.claim_queues[claim.transaction.coin_id] = ClaimQueue(claim)
        else:
            self.claim_queues[claim.transaction.coin_id].add(claim)
        return claim

    def dispute_claim(self, tx_origin, claim, witness=None):
        # Call the settlement contract's `dispute_claim` function to ensure the claim should be deleted
        assert claim.transaction.settlement_contract.dispute_claim(tx_origin, claim, witness)
        # Delete the claim
        claim_queue = self.claim_queues[claim.transaction.coin_id]
        claim_queue.remove(claim)

    def resolve_claim(self, tx_origin, claim, witness=None):
        # Call the settlement contract's `resolve_claim` function to ensure the claim should be resolved
        erc20_recipient = claim.transaction.settlement_contract.resolve_claim(tx_origin, claim, witness=witness)
        claim_queue = self.claim_queues[claim.transaction.coin_id]
        # Get the claim which is earliest in our claim queue
        recorded_claim = claim_queue.first()
        # Check that we are attempting to exit the earliest claim
        assert recorded_claim == claim
        # Check that the dispute_duration has passed
        assert self.eth.block_number >= claim.start_block_number + claim_queue.dispute_duration
        # Close the claim queue
        claim_queue.close()
        # Send the funds to the erc20_recipient
        self.erc20_contract.transferFrom(self.address, erc20_recipient, self.deposits[claim.transaction.coin_id].value)
        # Return the recipient
        return erc20_recipient
