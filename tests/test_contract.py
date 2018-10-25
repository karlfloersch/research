from pprint import PrettyPrinter

# pp = PrettyPrinter(indent=4)

def test_compilation(plasmaprime):
    assert plasmaprime

def test_deposits(plasmaprime):
    for i in range(10):
        plasmaprime.functions.deposit().transact({'value': i})
    total_deposits = plasmaprime.functions.total_deposits().call()
    assert total_deposits == 45

