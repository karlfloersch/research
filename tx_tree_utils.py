from ethereum.utils import sha3, bytes_to_int, int_to_bytes, encode_hex
import json
import random

# Tx array positions -- [parent_hash, parent_block, start, offset, recipient, signature]
PARENT_BLOCK_INDEX = 0
START_INDEX = 1
OFFSET_INDEX = 2
TO_INDEX = 3
FROM_INDEX = 4
SIG_INDEX = 5
DEPOSIT_PARENT_HASH = 32 * b'\x00'

class EphemDB():
    def __init__(self, kv=None):
        self.kv = kv or {}

    def get(self, k):
        return self.kv.get(k, None)

    def put(self, k, v):
        self.kv[k] = v

    def delete(self, k):
        del self.kv[k]

def fill_tx_list_with_notxs(txs):
    next_start_pos = 0
    full_tx_list = []
    for t in txs:
        # Add notx range if needed
        if t[START_INDEX] > next_start_pos:
            notx_offset = t[START_INDEX] - next_start_pos
            full_tx_list.append([0, next_start_pos, notx_offset, 'notx', 'notx'])
            next_start_pos += notx_offset
        assert t[START_INDEX] == next_start_pos
        next_start_pos += t[OFFSET_INDEX]
        full_tx_list.append(t)
    return full_tx_list

def construct_tree(db, nodes):
    if len(nodes) < 2:
        return nodes[0]
    remaining_nodes = []
    for i in range(0, len(nodes), 2):
        if i+1 == len(nodes):
            remaining_nodes.append(nodes[i])
            break
        new_value = b''.join([nodes[i], nodes[i+1]])
        new_sum = int_to_bytes(bytes_to_int(nodes[i+1][24:]) + bytes_to_int(nodes[i][24:])).rjust(8, b"\x00")
        new_hash = b''.join([sha3(new_value)[0:24], new_sum])
        print('Left:', encode_hex(nodes[i]), 'parent:', encode_hex(new_hash))
        print('Right:', encode_hex(nodes[i+1]), 'parent:', encode_hex(new_hash))
        db.put(new_hash, new_value)
        remaining_nodes.append(new_hash)
    return construct_tree(db, remaining_nodes)

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True

def get_proof_of_index(db, root, coin_id):
    if db.get(root) is None:
        return root
    proof = [root]

    def follow_path(node, total_offset, target):
        node_value = db.get(node)
        if is_json(node_value):
            return node_value
        left_sum = bytes_to_int(node_value[24:32])
        if left_sum + total_offset > target:
            proof.insert(0, ('left', node_value[32:]))
            return follow_path(node_value[0:32], total_offset, target)
        else:
            proof.insert(0, ('right', node_value[0:32]))
            return follow_path(node_value[32:], total_offset + left_sum, target)
    follow_path(root, 0, coin_id)
    return proof

# TODO: Clean this up! Eww!
def get_txs_at_index(db, root, range_start):
    if db.get(root) is None:
        return root
    root = db.get(root)

    def follow_path(node, total_offset, target):
        print(node)
        if is_json(node):
            return node
        left_sum = bytes_to_int(node[24:32])
        if left_sum + total_offset > target:
            return follow_path(db.get(node[0:32]), total_offset, target)
        else:
            return follow_path(db.get(node[32:]), total_offset + left_sum, target)

    return follow_path(root, 0, range_start)

def get_sum_hash_of_tx(tx):
    offset = int_to_bytes(tx[OFFSET_INDEX]).rjust(8, b"\x00")
    tx_hash = sha3(json.dumps(tx))
    return b''.join([tx_hash[:24], offset])

def make_block_from_txs(db, txs):
    merkle_leaves = []
    for t in txs:
        offset = int_to_bytes(t[OFFSET_INDEX]).rjust(8, b"\x00")
        tx_hash = sha3(json.dumps(t))
        leaf = b''.join([tx_hash[:24], offset])  # hash = leaf[:24] & sum = leaf[24:]
        db.put(leaf, json.dumps(t))
        merkle_leaves.append(leaf)
    merkle_root = construct_tree(db, merkle_leaves)
    return merkle_root

def generate_dummy_txs(num_txs, random_interval, total_deposits):
    txs = []
    last_start = 0
    for i in range(num_txs):
        next_offset = random.randint(1, random_interval)
        if last_start + next_offset > total_deposits:
            break
        if bool(random.getrandbits(1)):
            last_start += next_offset
            continue
        txs.append([0, last_start, next_offset, 'alice', 'alice', 'sig'])
        last_start += next_offset
    return txs

def generate_dummy_block(db, num_txs, random_interval, total_deposits):
    full_tx_list = fill_tx_list_with_notxs(generate_dummy_txs(num_txs, random_interval, total_deposits))
    merkle_leaves = []
    for t in full_tx_list:
        offset = int_to_bytes(t[OFFSET_INDEX]).rjust(8, b"\x00")
        tx_hash = sha3(json.dumps(t))
        leaf = b''.join([tx_hash[:24], offset])  # hash = leaf[:24] & sum = leaf[24:]
        db.put(leaf, json.dumps(t))
        merkle_leaves.append(leaf)
    merkle_root = construct_tree(db, merkle_leaves)
    return merkle_root
