class User:
    def __init__(self, address):
        self.address = address

    def sign(self, message):
        return {'message': message, 'signature': self.address}

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

class CommitLog:
    def __init__(self):
        self.commits = []

    def add_commit(self, commit):
        self.commits.append(commit)

class erc20Settlement:
    def __init__(self, address, token, commit_log):
        self.address = address
        self.token = token
        self.deposits = dict()
        self.total_deposits = 0
        self.exitable = {0: 0}
        self.commit_log = commit_log

    def deposit(self, depositor, deposit_amount):
        assert deposit_amount > 0
        # Make the transfer & update total balances
        self.token.transferFrom(depositor, self.address, deposit_amount)
        self.total_deposits += deposit_amount
        # Record this deposit
        deposit_start = self.total_deposits - deposit_amount
        deposit_end = self.total_deposits
        self.deposits[deposit_end] = {
            'start': deposit_start,
            'depositor': depositor,
            'plasmaBlockNumber': len(self.commit_log.commits)
        }
        # Make this deposit exitable
        self.exitable[deposit_end] = self.exitable[deposit_start]
        del self.exitable[deposit_start]

    def resolve(data):
        pass

# User definitions
alice = User('alice')
bob = User('bob')
# Contract definitions
omg = ERC20({alice.address: 1000, bob.address: 1000})
commit_log = CommitLog()
omgSettlementCt = erc20Settlement('omgSettlement', omg, commit_log)

# Begin tests
omgSettlementCt.deposit(alice.address, 500)
print('Settlement balance:', omg.balanceOf(omgSettlementCt.address), 'Alice balance:', omg.balanceOf(alice.address))
