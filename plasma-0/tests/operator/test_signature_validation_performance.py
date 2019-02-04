import time

def test_signature_validation_performance(w3, accts):
    raw_txs = []
    num_sigs = 1000
    print('Starting test')
    for i in range(num_sigs):
        test_tx = {
            'to': accts[0].address,
            'value': 1000000000,
            'gas': 2000000,
            'gasPrice': 234567897654321,
            'nonce': (i % len(accts)),
            'chainId': 1
        }
        raw_txs.append(accts[i % len(accts)].signTransaction(test_tx)['rawTransaction'])

    start_time = time.time()
    for r in raw_txs:
        w3.eth.account.recoverTransaction(r)
    print('Total time to recover', num_sigs, 'sigs:', time.time() - start_time)  # On my macbook I was processing 100 sigs per second.
