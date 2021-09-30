import copy
import pickle
from simple_rollup import generate_rollup

def test_generate_rollup():
    l1_chain: List[Block] = []
    expected_l2_chain: List[Block] = []

    for i in range(100):
        events: List[Event] = [{ "data": "event 1 data" }, { "data": "event 2 data" }]
        txs: List[Event] = [{ "data": "tx 1 data" }]
        block: Block = {
            "block_hash": 'blockhash' + str(i),
            "base_fee": 'basefee' + str(i),
            "block_number": i,
            "timestamp": i,
            "events": events,
            "txs": txs
        }
        expected_l2_chain.append(copy.deepcopy(block))
        l2_block_encoded = pickle.dumps(block)
        block["events"][0]["data"] = l2_block_encoded
        l1_chain.append(block)
    l2_chain = generate_rollup(l1_chain)

    for i in range(len(expected_l2_chain)):
        assert l2_chain[i]["timestamp"] == expected_l2_chain[i]["timestamp"]

    # Woot! We pulled the rollup out of the L1 chain!