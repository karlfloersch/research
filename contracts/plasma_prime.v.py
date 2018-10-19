# from ethereum.utils import sha3, int_to_bytes, bytes_to_int
# from tx_tree_utils import get_sum_hash_of_tx


EXIT_CHALLENGE_PERIOD: public(uint256)
EXIT_REFUTATION_GRACE_PERIOD: public(uint256)

operator: public(address)

next_blocknumber: public(uint256)
blocks: public(bytes32[uint256])
total_deposits: public(uint256[bytes32])

deposits: public({
    symbol: bytes32,
    next_blocknumber: uint256,
    start: uint256,
    offset: uint256,
    owner: address
}[uint256])
next_deposit_id: public(uint256)

exits: public({
    blocknumber: uint256,
    start: uint256,
    offset: uint256,
    challenge_blocks: uint256[uint256],
    challenge_txs: bytes32[uint256],
    num_challenges: uint256,
    owner: address
}[uint256])
next_exit_id: public(uint256)

ETH_symbol: public(bytes32)

@public
def __init__():
    self.EXIT_CHALLENGE_PERIOD = 5
    self.EXIT_REFUTATION_GRACE_PERIOD = 10
    self.ETH_symbol = 0x4554480000000000000000000000000000000000000000000000000000000000
    self.operator = msg.sender
    # TODO: Add self.exited_coin_ranges = []

@public
@payable
def deposit_eth():
    assert msg.value > 0
    # Record the deposit
    self.deposits[self.next_deposit_id] = {
        symbol: self.ETH_symbol,
        next_blocknumber: self.next_blocknumber,
        start: self.total_deposits[self.ETH_symbol],
        offset: as_unitless_number(msg.value),
        owner: msg.sender
    }
    self.next_deposit_id += 1
    # Update total deposits
    self.total_deposits[self.ETH_symbol] += as_unitless_number(msg.value)

@public
def add_block(plasma_blockhash: bytes32):
    assert msg.sender == self.operator
    self.blocks[self.next_blocknumber] = plasma_blockhash
    self.next_blocknumber += 1

@public
def exit(symbol: bytes32, start: uint256, offset: uint256, owner: address):
    assert start + offset < self.total_deposits[symbol]
    self.exits[self.next_exit_id].blocknumber = self.next_blocknumber
    self.exits[self.next_exit_id].start = start
    self.exits[self.next_exit_id].offset = offset
    self.exits[self.next_exit_id].owner = owner
    self.next_exit_id += 1
    # TODO: Add bond for exit

# def verify_merkle_proof(self, blockhash, tx, proof):
#     h = get_sum_hash_of_tx(tx)
#     for i in range(0, len(proof)-1):
#         if proof[i][0] == 'left':
#             new_value = b''.join([h, proof[i][1]])
#         else:
#             new_value = b''.join([proof[i][1], h])
#         new_sum = int_to_bytes(bytes_to_int(h[32:]) + bytes_to_int(proof[i][1][32:])).rjust(8, b"\x00")
#         h = b''.join([sha3(new_value), new_sum])
#     return h == proof[-1]

# TODO: Finish converting this function!
@public
def challenge_coin(exit_index: uint256, coin_id: uint256, blocknumber_of_spend: uint256, tx: bytes[1024], proof: bytes32[100]):
    # Check that the challenge period isn't up
    assert block.number < self.exits[exit_index].blocknumber + self.EXIT_CHALLENGE_PERIOD
    # Check that the challenge is of the correct coin
    assert self.exits[exit_index].start <= coin_id and coin_id < self.exits[exit_index].start + self.exits[exit_index].offset
    # # Verify that the owner is not the exit owner (why would you challenge your own coin?)
    # assert tx['contents']['owner'] != self.exits[exit_index]['owner']
    # # Check that the transaction is in the specified block
    # # assert self.verify_merkle_proof(self.blocks[blocknumber_of_spend], tx, proof)
    # # Record challenge
    # self.exits[exit_index]['challenge_blocks'].append(blocknumber_of_spend)
    # self.exits[exit_index]['challenge_txs'].append(get_sum_hash_of_tx(tx))

# def refute_challenge(self, exit_index, challenge_index, coin_id, blocknumber_of_spend, tx, proof):
#     # Check that the challenge is of the correct coin
#     assert self.exits[exit_index]['start'] <= coin_id and coin_id < self.exits[exit_index]['start'] + self.exits[exit_index]['offset']
#     # Check that the blocknumber of the refutation is after the challenge block
#     assert blocknumber_of_spend > self.exits[exit_index]['challenge_blocks'][challenge_index]
#     # Check that the transaction is in the specified block
#     assert self.verify_merkle_proof(self.blocks[blocknumber_of_spend], tx, proof)
#     # Check that the transaction references the challenge tx
#     assert tx['contents']['prev_tx'] == str(self.exits[exit_index]['challenge_txs'][challenge_index])
#     # Delete invalid challenge. TODO: Forfit bond
#     del self.exits[exit_index]['challenge_blocks'][challenge_index]
#     del self.exits[exit_index]['challenge_txs'][challenge_index]

# def withdraw(self, exit_index):
#     assert self.time > self.exits[exit_index]['timestamp'] + EXIT_REFUTATION_GRACE_PERIOD
#     assert len(self.exits[exit_index]['challenge_blocks']) == 0
#     print('successful withdrawl! Sending money to ', self.exits[exit_index]['owner'])
#     self.exited_coin_ranges.append([self.exits[exit_index]['start'], self.exits[exit_index]['offset']])
