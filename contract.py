EXIT_CHALLENGE_PERIOD = 10
EXIT_REFUTATION_GRACE_PERIOD = 15

class PlasmaContract():

    def __init__(self):
        self.blocknumber = 0
        self.blocks = []
        self.total_deposits = {}
        self.deposits = {}
        self.time = 0
        self.exits = []

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

    def exit(self, token, start, offset, owner):
        assert start + offset < self.total_deposits[token]
        self.exits.append({
            'timestamp': self.time,
            'start': start,
            'offset': offset,
            'challenge_blocks': [],
            'owner': owner
        })
        # TODO: Add bond for exit

    def challenge_spent_coin(self, exit_index, coin_id, blocknumber_of_spend, proof):
        # Check that the challenge period isn't up
        assert self.time < self.exits[exit_index]['timestamp'] + EXIT_CHALLENGE_PERIOD
        # Check that the challenge is of the correct coin
        assert self.exits[exit_index]['start'] < coin_id and coin_id < self.exits[exit_index]['start'] + self.exits[exit_index]['offset']
        # TODO: Actually implement proof checker
        if proof is False:
            return
        self.exits[exit_index]['challenge_blocks'].append(blocknumber_of_spend)

    def refute_challenge(self, exit_index, challenge_index, coin_id, blocknumber_of_spend, proof):
        # Check that the challenge is of the correct coin
        assert self.exits[exit_index]['start'] < coin_id and coin_id < self.exits[exit_index]['start'] + self.exits[exit_index]['offset']
        assert blocknumber_of_spend > self.exits[exit_index]['challenge_blocks'][challenge_index]
        # TODO: Implement proof checker--Check inclusion & that the tx spends the challenge coin
        if proof is False:
            return
        del self.exits[exit_index]['challenge_blocks'][challenge_index]

    def withdraw(self, exit_index):
        assert self.time > self.exits[exit_index]['timestamp'] + EXIT_REFUTATION_GRACE_PERIOD
        assert len(self.exits[exit_index]['challenge_blocks']) == 0
        print('successful withdrawl! Sending money to ', self.exits[exit_index]['owner'])
