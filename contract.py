
class PlasmaContract():

    def __init__(self):
        self.blocknumber = 0
        self.blocks = []
        self.total_deposits = {}
        self.deposits = {}

    def deposit(self, token, amount, owner):
        if amount < 1:
            raise Exception('Deposit must be positive!')
        if token not in self.total_deposits:
            self.total_deposits[token] = 0
        next_block = self.blocknumber+1
        if next_block not in self.deposits:
            self.deposits[next_block] = []
        # Record the deposit
        deposit_record = {
            'token_name': token,
            'start': self.total_deposits[token],
            'amount': amount,
            'owner': owner
        }
        self.deposits[next_block].append(deposit_record)
        self.total_deposits[token] += amount

    def add_block(self, blockhash):
        self.blocks.append(blockhash)
        self.blocknumber += 1
