####### DEPRECATED #######
####### DEPRECATED #######
####### DEPRECATED #######
####### DEPRECATED #######
####### DEPRECATED #######
####### DEPRECATED #######





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
    start: uint256,
    offset: uint256,
    challenge_count: uint256,
}[uint256])
challenges: public(
{
    exit_id: uint256,
    ongoing: bool,
    token_index: uint256,
}[uint256])
exit_nonce: public(uint256)
challenge_nonce: public(uint256)

# period (of ethereum blocks) during which an exit can be challenged
CHALLENGE_PERIOD: constant(uint256) = 20
# minimum number of ethereum blocks between new plasma blocks
PLASMA_BLOCK_INTERVAL: constant(uint256) = 10
#
MAX_TREE_DEPTH: constant(uint256) = 8

# @public
# def ecrecover_util(message_hash: bytes32, signature: bytes[65]) -> address:
#     v: uint256 = extract32(slice(signature, start=0, len=32), 0, type=uint256)
#     r: uint256 = extract32(slice(signature, start=32, len=64), 0, type=uint256)
#     s: bytes[1] = slice(signature, start=64, len=1)
#     s_pad: uint256 = extract32(s, 0, type=uint256)
#
#     addr: address = ecrecover(message_hash, v, r, s_pad)
#     return addr

@public
def addr_to_bytes(addr: address) -> bytes[20]:
    addr_bytes32: bytes[32] = concat(convert(addr, bytes32), "")
    return slice(addr_bytes32, start=12, len=20)

@public
def plasma_message_hash(
        sender: address,
        recipient: address,
        start: uint256,
        offset: uint256,
) -> bytes32:
    return sha3(concat(
        self.addr_to_bytes(sender),
        self.addr_to_bytes(recipient),
        convert(start, bytes32),
        convert(offset, bytes32),
    ))

@public
def tx_hash(
        sender: address,
        recipient: address,
        start: uint256,
        offset: uint256,
        sig_v: uint256,
        sig_r: uint256,
        sig_s: uint256,
) -> bytes32:
    return sha3(concat(
        self.addr_to_bytes(sender),
        self.addr_to_bytes(recipient),
        convert(start, bytes32),
        convert(offset, bytes32),
        convert(sig_v, bytes32),
        convert(sig_r, bytes32),
        convert(sig_s, bytes32),
    ))

@public
def __init__():
    self.operator = msg.sender
    self.total_deposits = 0
    self.plasma_block_number = 0
    self.exit_nonce = 0
    self.last_publish = 0
    self.challenge_nonce = 0

@public
@payable
def deposit() -> uint256:
    r: uint256 = as_unitless_number(self.total_deposits)
    self.deposits[msg.sender] += msg.value
    self.total_deposits += msg.value
    return r

@public
def publish_hash(block_hash: bytes32):
    assert msg.sender == self.operator
    assert block.number >= self.last_publish + PLASMA_BLOCK_INTERVAL

    self.hash_chain[self.plasma_block_number] = block_hash
    self.plasma_block_number += 1
    self.last_publish = block.number

@public
def submit_exit(bn: uint256, start: uint256, offset: uint256) -> uint256:
    assert bn < self.plasma_block_number
    assert offset > 0
    assert offset <= as_unitless_number(self.total_deposits)

    en: uint256 = self.exit_nonce
    self.exits[en].owner = msg.sender
    self.exits[en].plasma_block = bn
    self.exits[en].eth_block = block.number
    self.exits[en].start = start
    self.exits[en].offset = offset
    self.exits[en].challenge_count = 0
    self.exit_nonce += 1
    return en

@public
def finalize_exit(exit_id: uint256):
    assert block.number >= self.exits[exit_id].eth_block + CHALLENGE_PERIOD
    assert self.exits[exit_id].challenge_count == 0

    send(self.exits[exit_id].owner, as_wei_value(self.exits[exit_id].offset, 'wei'))
    self.total_deposits -= as_wei_value(self.exits[exit_id].offset, 'wei')

@public
def challenge_completeness(
        exit_id: uint256,
        token_index: uint256,
) -> uint256:
    # check the exit being challenged exists
    assert exit_id < self.exit_nonce

    # check the token index being challenged is in the range being exited
    assert token_index >= self.exits[exit_id].start
    assert token_index < self.exits[exit_id].start + self.exits[exit_id].offset

    # store challenge
    cn: uint256 = self.challenge_nonce
    self.challenges[cn].exit_id = exit_id
    self.challenges[cn].ongoing = True
    self.challenges[cn].token_index = token_index
    self.exits[exit_id].challenge_count += 1

    self.challenge_nonce += 1
    return cn

@public
def respond_completeness(
        challenge_id: uint256,
        sender: address,
        recipient: address,
        start: uint256,
        offset: uint256,
        sig_v: uint256,
        sig_r: uint256,
        sig_s: uint256,
        proof: bytes32[8],
):
    assert self.challenges[challenge_id].ongoing == True

    exit_id: uint256 = self.challenges[challenge_id].exit_id
    exit_owner: address = self.exits[exit_id].owner
    exit_plasma_block: uint256 = self.exits[exit_id].plasma_block
    challenged_index: uint256 = self.challenges[challenge_id].token_index

    # compute message hash
    message_hash: bytes32 = self.plasma_message_hash(sender, recipient, start, offset)

    # check transaction is signed correctly
    addr: address = ecrecover(message_hash, sig_v, sig_r, sig_s)
    assert addr == sender

    # check exit owner is indeed recipient
    assert recipient == exit_owner

    # check transaction covers challenged index
    assert challenged_index >= start
    assert challenged_index < (start + offset)

    # check transaction was included in plasma block hash
    root: bytes32 = self.tx_hash(
        sender,
        recipient,
        start,
        offset,
        sig_v,
        sig_r,
        sig_s,
    )
    for i in range(8):
        if convert(proof[i], uint256) == 0:
            break
        root = sha3(concat(root, proof[i]))
    assert root == self.hash_chain[exit_plasma_block]

    # response was successful
    self.challenges[challenge_id].ongoing = False
    self.exits[exit_id].challenge_count -= 1
