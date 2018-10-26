
operator: public(address)
deposits: public(wei_value[address])
total_deposits: public(wei_value)
plasma_block_number: public(uint256)
last_publish: public(uint256) # ethereum block number of most recent plasma block
hash_chain: public(bytes32[uint256])
exits: public(
{
    owner: address,
    plasma_block: uint256,
    eth_block: uint256,
    start: wei_value,
    offset: wei_value
}[uint256])
exit_nonce: public(uint256)

# period (of ethereum blocks) during which an exit can be challenged
CHALLENGE_PERIOD: constant(uint256) = 20
# minimum number of ethereum blocks between new plasma blocks
PLASMA_BLOCK_INTERVAL: constant(uint256) = 10

@public
def __init__():
    self.operator = msg.sender
    self.total_deposits = 0
    self.plasma_block_number = 0
    self.exit_nonce = 0
    self.last_publish = 0

@public
@payable
def deposit():
    self.deposits[msg.sender] += msg.value
    self.total_deposits += msg.value

@public
def publish_hash(block_hash: bytes32):
    assert msg.sender == self.operator
    assert block.number >= self.last_publish + PLASMA_BLOCK_INTERVAL

    self.hash_chain[self.plasma_block_number] = block_hash
    self.plasma_block_number += 1
    self.last_publish = block.number

@public
def submit_exit(bn: uint256, start: wei_value, offset: wei_value) -> uint256:
    assert bn <= self.plasma_block_number
    assert offset > 0

    self.exits[self.exit_nonce].owner = msg.sender
    self.exits[self.exit_nonce].plasma_block = bn
    self.exits[self.exit_nonce].eth_block = block.number
    self.exits[self.exit_nonce].start = start
    self.exits[self.exit_nonce].offset = offset

    exit_id : uint256 = self.exit_nonce
    self.exit_nonce += 1
    return exit_id

@public
def finalize_exit(exit_id: uint256):
    assert block.number >= self.exits[exit_id].eth_block + CHALLENGE_PERIOD

    send(self.exits[exit_id].owner, self.exits[exit_id].offset)
    self.total_deposits -= self.exits[exit_id].offset

