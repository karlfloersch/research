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
    def __init__(self, coin_id, settlement_contract, plasma_block_number):
        self.coin_id = coin_id
        self.settlement_contract = settlement_contract
        self.plasma_block_number = plasma_block_number

class CashTransaction(Transaction):
    def __init__(self, coin_id, sender, recipient, plasma_block_number, settlement_contract):
        Transaction.__init__(self, coin_id, settlement_contract, plasma_block_number)
        self.sender = sender
        self.recipient = recipient

class Erc20Deposit(Transaction):
    def __init__(self, coin_id, recipient, value, settlement_contract, plasma_block_number):
        Transaction.__init__(self, coin_id, settlement_contract, plasma_block_number)
        self.recipient = recipient
        self.value = value

class Claim:
    def __init__(self, eth_block_number, transaction):
        assert isinstance(transaction, Transaction)
        self.start_block_number = eth_block_number
        self.transaction = transaction

class ClaimQueue:
    def __init__(self, initial_claim):
        self.claims = {}
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
    def __init__(self, eth, address, token):
        self.eth = eth
        self.address = address
        self.token = token
        self.deposits = dict()
        self.total_deposits = 0
        self.commitments = []
        self.claim_queues = {}
        self.resolved_claims = []

    def deposit_ERC20(self, depositor, deposit_amount, settlement_contract):
        assert deposit_amount > 0
        # Make the transfer
        self.token.transferFrom(depositor, self.address, deposit_amount)
        # Record the deposit
        deposit = Erc20Deposit(self.total_deposits, depositor, deposit_amount, settlement_contract, len(self.commitments))
        self.deposits[deposit.coin_id] = deposit
        # Increment total deposits
        self.total_deposits += 1
        # Return deposit record
        return deposit

    def add_commitment(self, commit):
        self.commitments.append(commit)

    def _validate_transaction(self, transaction):
        if transaction is None:
            return False
        assert transaction in self.commitments[transaction.plasma_block_number]
        assert self.deposits[transaction.coin_id] and self.deposits[transaction.coin_id].plasma_block_number <= transaction.plasma_block_number
        return True

    def _validate_deposit(self, deposit):
        if deposit is None:
            return False
        assert deposit == self.deposits[deposit.coin_id]
        return True

    def submit_claim(self, transaction=None, deposit=None):
        # Make sure we submitted either a valid transaction or deposit
        assert self._validate_transaction(transaction) or self._validate_deposit(deposit)
        # Create a claim for either the transaction or deposit
        claim = Claim(self.eth.block_number, transaction) if transaction is not None else Claim(self.eth.block_number, deposit)
        # Create a new claim
        if claim.transaction.coin_id not in self.claim_queues:
            self.claim_queues[claim.transaction.coin_id] = ClaimQueue(claim)
        else:
            self.claim_queues[claim.transaction.coin_id].add(claim)
        return claim

    def dispute_claim(self, msg_sender, claim):
        # Ensure dispute can only be called by the appropriate settlement contract. No lying about msg_sender allowed! ;)
        assert msg_sender == claim.transaction.settlement_contract
        # Delete the claim
        claim_queue = self.claim_queues[claim.transaction.coin_id]
        claim_queue.remove(claim)

    def resolve_claim(self, claim):
        claim_queue = self.claim_queues[claim.coin.id]
        # Get the claim which is earliest in our claim queue
        recorded_claim = claim_queue.first()
        # Check that we are attempting to exit the earliest claim
        assert recorded_claim == claim
        # Check that the dispute_duration has passed
        assert self.eth.block_number > claim.start_block_number + claim_queue.dispute_duration
        # Close the claim queue
        claim_queue.close()
        # Send the funds
        self.token.transferFrom(self.address, claim.claimant, claim.coin.value)


class TransferSettlementContract:
    dispute_duration = 10

    def __init__(self, parent_settlement_contract):
        self.parent = parent_settlement_contract

    def dispute_claim(self, claim, spend_transaction):
        # Check these are spends of the same coin
        assert claim.transaction.coin_id == spend_transaction.coin_id
        # Check that the sender is correct
        assert claim.transaction.recipient == spend_transaction.sender
        # Check that the spend is after the claim transaction
        assert claim.transaction.plasma_block_number <= spend_transaction.plasma_block_number
        self.parent.dispute_claim(self, claim)

    def resolve_claim(self, claim):
        pass
