class Eth:
    ''' Eth object contains information about the mocked Ethereum blockchain '''
    def __init__(self, block_number):
        self.block_number = block_number

class User:
    '''
    User class which is given an address and can be used to generate fake signatures.
    Note addresses here are human-readable & signatures are not secure--all to facilitate testing.
    '''

    def __init__(self, address):
        self.address = address

    def sign(self, message):
        return {'message': message, 'signature': self.address}

    def __str__(self):
        return self.address

class ERC20:
    ''' ERC20-like python contract '''

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
