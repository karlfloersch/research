class Eth:
    def __init__(self, block_number):
        self.block_number = block_number

class User:
    def __init__(self, address):
        self.address = address

    def sign(self, message):
        return {'message': message, 'signature': self.address}

    def __str__(self):
        return self.address

class ERC20:
    def __init__(self, initial_balances):
        self.balances = initial_balances

    def balanceOf(self, token_holder):
        return self.balances[token_holder]

    def transferFrom(self, sender, recipient, tokens):
        assert self.balances[sender] >= tokens
        self.balances[sender] -= tokens
        if recipient not in self.balances:
            self.balances[recipient] = 0
        self.balances[recipient] += tokens
        return True

class Transaction:
    def __init__(self, coin_id, plasma_block_number, settlement_contract, parameters):
        for key in parameters:
            setattr(self, key, parameters[key])
        self.coin_id = coin_id
        self.settlement_contract = settlement_contract
        self.plasma_block_number = plasma_block_number

class Erc20Deposit(Transaction):
    def __init__(self, coin_id, plasma_block_number, value, settlement_contract, parameters):
        Transaction.__init__(self, coin_id, plasma_block_number, settlement_contract, parameters)
        self.value = value

class Claim:
    def __init__(self, eth_block_number, transaction):
        assert isinstance(transaction, Transaction)
        self.transaction = transaction
        self.start_block_number = eth_block_number

class ClaimQueue:
    def __init__(self, initial_claim):
        self.claims = {}
        # TODO: Dispute duration should change for everything to the right of the plasma_block_number
        self.dispute_duration = 0
        self.is_open = True
        self.add(initial_claim)

    def add(self, claim):
        assert self.is_open
        if self.dispute_duration < claim.transaction.settlement_contract.dispute_duration:
            self.dispute_duration = claim.transaction.settlement_contract.dispute_duration
        self.claims[claim.transaction.plasma_block_number] = claim

    def __len__(self):
        return len(self.claims)

    def remove(self, claim):
        assert self.is_open
        del self.claims[claim.transaction.plasma_block_number]

    def first(self):
        return self.claims[sorted(self.claims.keys())[0]]

    def close(self):
        self.is_open = False

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
