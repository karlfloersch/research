from ethereum.utils import sha3, bytes_to_int, int_to_bytes, encode_hex
import pprint
import json
pp = pprint.PrettyPrinter(indent=4)

class EphemDB():
    def __init__(self, kv=None):
        self.kv = kv or {}

    def get(self, k):
        return self.kv.get(k, None)

    def put(self, k, v):
        self.kv[k] = v

    def delete(self, k):
        del self.kv[k]

# newh = sha3(h + h)
# db.put(newh, h + h)

def fill_tx_list_with_notxs(txs):
    if len(txs) < 2:
        # For now ignore the edge case with one tx
        raise Exception('Too few txs')
    next_start_pos = 0
    full_tx_list = []
    for t in txs:
        # Add notx range if needed
        if t['contents']['start'] > next_start_pos:
            notx_offset = t['contents']['start'] - next_start_pos
            full_tx_list.append({'type': 'notx', 'contents': {'start': next_start_pos, 'offset': notx_offset}})
            next_start_pos += notx_offset
        assert t['contents']['start'] == next_start_pos
        next_start_pos += t['contents']['offset']
        full_tx_list.append(t)
    pp.pprint(full_tx_list)
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
        new_sum = int_to_bytes(bytes_to_int(nodes[i+1][32:]) + bytes_to_int(nodes[i][32:])).rjust(8, b"\x00")
        print('A new sum:', bytes_to_int(new_sum))
        new_hash = b''.join([sha3(new_value), new_sum])
        db.put(new_hash, new_value)
        remaining_nodes.append(new_hash)
    return construct_tree(db, remaining_nodes)

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True

def get_txs_at_index(db, root, range_start):
    if db.get(root) is None:
        return root
    root = db.get(root)

    def follow_path(node, total_offset, target):
        print(node)
        if is_json(node):
            return node
        left_sum = bytes_to_int(node[32:40])
        if left_sum + total_offset > target:
            return follow_path(db.get(node[0:40]), total_offset, target)
        else:
            return follow_path(db.get(node[40:]), total_offset + left_sum, target)

    return follow_path(root, 0, range_start)

# tx = ['send', [[[parent_hash, parent_block],...], start, offset, recipient], signature]
txs = [
    {'type:': 'send', 'contents': {'start': 0, 'offset': 3, 'owner': 'alice'}, 'sig': 'sig'},
    {'type:': 'send', 'contents': {'start': 6, 'offset': 3, 'owner': 'bob'}, 'sig': 'sig'},
    {'type:': 'send', 'contents': {'start': 9, 'offset': 1, 'owner': 'jing'}, 'sig': 'sig'},
    {'type:': 'send', 'contents': {'start': 10, 'offset': 1, 'owner': 'jing'}, 'sig': 'sig'}
]

db = EphemDB()
full_tx_list = fill_tx_list_with_notxs(txs)
merkle_leaves = []
for t in full_tx_list:
    offset = int_to_bytes(t['contents']['offset']).rjust(8, b"\x00")
    tx_hash = sha3(json.dumps(t))
    leaf = b''.join([tx_hash, offset])  # hash = leaf[:32] & sum = leaf[32:]
    db.put(leaf, json.dumps(t))
    merkle_leaves.append(leaf)

merkle_root = construct_tree(db, merkle_leaves)
print('~~~~')
print(get_txs_at_index(db, merkle_root, 4))

class Node():
    pass
