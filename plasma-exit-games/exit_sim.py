# import sys

# Color lib for pretty output
class bcolors:
    GREEN = '\033[92m'
    PINK = '\033[95m'
    PURPLE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
def red(string):
    return bcolors.RED + string + bcolors.ENDC
def green(string):
    return bcolors.GREEN + string + bcolors.ENDC
def yellow(string):
    return bcolors.YELLOW + string + bcolors.ENDC
def purp(string):
    return bcolors.PURPLE + string + bcolors.ENDC
def pink(string):
    return bcolors.PINK + string + bcolors.ENDC

# Data Structures
class Coin:
    def __init__(self, id, prev_block, sender, recipient):
        self.id = id
        self.prev_block = prev_block
        self.sender = sender
        self.recipient = recipient

    def __str__(self):
        coin = 'id: ' + purp(str(self.id))
        prev_block = ', prev_block: ' + purp(str(self.prev_block))
        sender = ', sender: ' + self.sender
        recipient = ', recipient: ' + self.recipient
        return str('[' + coin + prev_block + sender + recipient + ']')

class Block:
    def __init__(self, coins):
        self.coins = coins

    def __str__(self):
        output = ''
        for coin in self.coins:
            output += str(coin) + '\n'
        return output

    def includes(self, coin):
        return coin in self.coins

class Exit:
    def __init__(self, time, coin_id, owner, block):
        self.time = time
        self.coin_id = coin_id
        self.owner = owner
        self.block = block

    def cancel(self, spend_coin):
        if (self.block == spend_coin.prev_block and self.owner == spend_coin.sender):
            return True
        return False

def validate_coin(state, coin):
    if state[coin.id]['block'] != coin.prev_block:
        raise Exception('Invalid prev_block: ' + str(coin.prev_block) + '. Expected: ' + str(state[coin.id]['block']))
    if coin.sender != state[coin.id]['owner']:
        raise Exception('Invalid sender:' + str(coin.sender) + '. Expected: ' + state[coin.id].owner)
    return True

def apply_block(state, block):
    for coin in block.coins:
        print(coin)
        if coin.sender == DEPOSIT or validate_coin(state, coin):
            state[coin.id] = {
                'block': state['block'],
                'owner': coin.recipient
            }
        else:
            raise Exception('Invalid tx:' + str(coin))
    state['block'] += 1

def apply_blocks(state, blocks):
    for block in blocks:
        apply_block(state, block)
    return state

DEPOSIT = pink('DEPOSIT')
alice = yellow('alice')
invalid_alice = red('invalid_alice')
bob = green('bob')
invalid_bob = red('invalid_bob')

# Test spent coin
# Process genesis block
state = {'block': 0}
blocks = [
    Block([Coin(0, 0, DEPOSIT, alice)]),
    Block([Coin(0, 0, alice, bob)]),
    Block([Coin(0, 1, bob, alice)])
]
state = apply_blocks(state, blocks)
print(state)
