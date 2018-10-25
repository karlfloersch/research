operator: public(address)
deposits: public(wei_value[address])
total_deposits: public(wei_value)
block_number: public(uint256)
hash_chain: public(bytes32[uint256])

@public
def __init__():
    self.operator = msg.sender
    self.total_deposits = 0
    self.block_number = 0

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
    self.block_number = bn + 1
