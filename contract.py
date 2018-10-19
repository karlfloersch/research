from ethereum.utils import sha3, int_to_bytes, bytes_to_int
from tx_tree_utils import get_sum_hash_of_tx


EXIT_CHALLENGE_PERIOD = 10
EXIT_REFUTATION_GRACE_PERIOD = 15

class PlasmaContract():

    def __init__(self):
        self.blocknumber = 0
        self.blocks = []
        self.total_deposits = {}
        self.deposits = {}
        self.exited_coin_ranges = []
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
            'challenge_txs': [],
            'owner': owner
        })
        # TODO: Add bond for exit

    def verify_merkle_proof(self, blockhash, tx, proof):
        h = get_sum_hash_of_tx(tx)
        for i in range(0, len(proof)-1):
            if proof[i][0] == 'left':
                new_value = b''.join([h, proof[i][1]])
            else:
                new_value = b''.join([proof[i][1], h])
            new_sum = int_to_bytes(bytes_to_int(h[24:]) + bytes_to_int(proof[i][1][24:])).rjust(8, b"\x00")
            h = b''.join([sha3(new_value)[:24], new_sum])
        return h == proof[-1]

    def challenge_coin(self, exit_index, coin_id, blocknumber_of_spend, tx, proof):
        # Check that the challenge period isn't up
        assert self.time < self.exits[exit_index]['timestamp'] + EXIT_CHALLENGE_PERIOD
        # Check that the challenge is of the correct coin
        assert self.exits[exit_index]['start'] <= coin_id and coin_id < self.exits[exit_index]['start'] + self.exits[exit_index]['offset']
        # Verify that the owner is not the exit owner (why would you challenge your own coin?)
        assert tx['contents']['owner'] != self.exits[exit_index]['owner']
        # Check that the transaction is in the specified block
        assert self.verify_merkle_proof(self.blocks[blocknumber_of_spend], tx, proof)
        # Record challenge
        self.exits[exit_index]['challenge_blocks'].append(blocknumber_of_spend)
        self.exits[exit_index]['challenge_txs'].append(get_sum_hash_of_tx(tx))

    def refute_challenge(self, exit_index, challenge_index, coin_id, blocknumber_of_spend, tx, proof):
        # Check that the challenge is of the correct coin
        assert self.exits[exit_index]['start'] <= coin_id and coin_id < self.exits[exit_index]['start'] + self.exits[exit_index]['offset']
        # Check that the blocknumber of the refutation is after the challenge block
        assert blocknumber_of_spend > self.exits[exit_index]['challenge_blocks'][challenge_index]
        # Check that the transaction is in the specified block
        assert self.verify_merkle_proof(self.blocks[blocknumber_of_spend], tx, proof)
        # Check that the transaction references the challenge tx
        assert tx['contents']['prev_tx'] == str(self.exits[exit_index]['challenge_txs'][challenge_index])
        # Delete invalid challenge. TODO: Forfit bond
        del self.exits[exit_index]['challenge_blocks'][challenge_index]
        del self.exits[exit_index]['challenge_txs'][challenge_index]

    def withdraw(self, exit_index):
        assert self.time > self.exits[exit_index]['timestamp'] + EXIT_REFUTATION_GRACE_PERIOD
        assert len(self.exits[exit_index]['challenge_blocks']) == 0
        print('successful withdrawl! Sending money to ', self.exits[exit_index]['owner'])
        self.exited_coin_ranges.append([self.exits[exit_index]['start'], self.exits[exit_index]['offset']])
