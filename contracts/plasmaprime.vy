# units: {
    # plasma_time: "Plasma Time"
# }

operator: public(address)
deposits: public(wei_value[address])
total_deposits: public(wei_value)
block_number: public(uint256)
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

EXIT_PERIOD: constant(uint256) = 20

@public
def __init__():
    self.operator = msg.sender
    self.total_deposits = 0
    self.block_number = 1
    self.exit_nonce = 0

@public
@payable
def deposit():
    self.deposits[msg.sender] += msg.value
    self.total_deposits += msg.value

@public
def publish_hash(block_hash: bytes32):
    assert msg.sender == self.operator

    bn: uint256 = self.block_number
    self.hash_chain[bn] = block_hash
    self.block_number += 1

@public
def submit_exit(bn: uint256, start: wei_value, offset: wei_value) -> uint256:
    assert self.block_number > bn
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
    assert block.number >= self.exits[exit_id].eth_block + EXIT_PERIOD

    send(self.exits[exit_id].owner, self.exits[exit_id].offset)
    self.total_deposits -= self.exits[exit_id].offset
