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
    def __init__(self, number, coins):
        self.coins = coins
        self.number = number

    def __str__(self):
        output = ''
        for coin in self.coins:
            output += str(coin) + '\n'
        return output

    def includes(self, coin):
        return coin in self.coins

class Exit:
    def __init__(self, eth_block_number, coin_id, owner, plasma_block):
        self.eth_block_number = eth_block_number
        self.coin_id = coin_id
        self.owner = owner
        self.plasma_block = plasma_block

    def cancel(self, spend_coin):
        if (self.plasma_block == spend_coin.prev_plasma_block and self.owner == spend_coin.sender):
            return True
        return False

class PlasmaContract:
    def __init__(self):
        self.eth_block_number = 0  # the current eth block number -- this can be used to simulate time passing in the exit game
        self.exit_queues = dict()  # coin_id -> plasma_block_number -> exit_object
        self.exited_coins = dict()  # coin_id -> True / False

    def exit_coin(self, coin_id, owner, plasma_block):
        new_exit = Exit(self.eth_block_number, coin_id, owner, plasma_block)  # create a new exit object
        if coin_id not in self.exit_queues:
            self.exit_queues[coin_id] = dict()
        self.exit_queues[coin_id][new_exit.plasma_block.number] = new_exit  # add this exit to the queue
        return new_exit  # return our new exit object

    def cancel_exit(self, exit, coin_spend):
        # Check that the coin which spends the exit is from the owner
        # assert exit.owner == coin_spend.sender
        # ...and that the coin which spends the exit references that coin with prev_block
        # assert exit.plasma_block == coin_spend.prev_block
        # ...and that the exit is really in the block
        # ...
        # Then cancel the exit
        # del self.exit_queues[exit.coin_id][exit.plasma_block.number]
        pass

    def finalize_exit(self, exit):
        # Check if the coin has already been exited
        # assert self.exit in self.exited_coins
        # ...and that the exit period is over
        # assert exit.eth_block_number + EXIT_PERIOD < self.eth_block_number
        # Determine the exit winner
        # winner = the lowest `plasma_block_number` inside of self.exit_queues[exit.coin_id]
        # Record this exit
        # self.exited_coins[exit.exit_id] = True
        pass

def validate_coin(state, coin):
    ''' Check if a particular state & coin combination is valid '''
    if state[coin.id]['block'] != coin.prev_block:
        raise Exception('Invalid prev_block: ' + str(coin.prev_block) + '. Expected: ' + str(state[coin.id]['block']))
    if coin.sender != state[coin.id]['owner']:
        raise Exception('Invalid sender:' + str(coin.sender) + '. Expected: ' + state[coin.id].owner)
    return True

def apply_block(state, block):
    ''' Applies the block & thows if the block is invalid '''
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
alice_sigs = [yellow('alice1'), yellow('alice2')]
bob_sigs = [green('bob')]

# TODO: Test spent coin
state = {'block': 0}  # Genesis state
coins = [  # Coins
    Coin(0, 0, DEPOSIT, alice_sigs[0]),
    Coin(0, 0, alice_sigs[0], bob_sigs[0]),
    Coin(0, 1, bob_sigs[0], alice_sigs[1])
]
blocks = [  # Blocks
    Block(0, [coins[0]]),
    Block(1, [coins[1]]),
    Block(2, [coins[2]])
]
# State after having applied blocks -- this just checks validity. Note validity is not checked in the smart contract
state = apply_blocks(state, blocks)
print(state)  # this state stuff is mostly for checking if we have any invalid blocks

# Now that we know all the blocks are valid and can calculate the correct owner, let's try exiting a spent coin
plasma_contract = PlasmaContract()  # create new Plasma contract
plasma_contract.exit_coin(0, alice_sigs[0], blocks[0])  # try to exit spent coin
# TODO: Challenge spent coin
# TODO: Test exiting an invalid coin and then reacting
# TODO: Test normal exits... test everything!
