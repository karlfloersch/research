from contract import PlasmaContract
from tx_tree_utils import EphemDB, generate_dummy_block
import pprint
pp = pprint.PrettyPrinter(indent=4)


class Operator():
    def __init__(self):
        self.db = EphemDB()
        self.contract = PlasmaContract()
        self.contract.deposit('ETH', 10000, 'alice')

    def tick(self):
        new_blockhash = generate_dummy_block(self.db, 100, 5, 10000)
        self.contract.add_block(new_blockhash)

operator = Operator()
operator.tick()
operator.tick()
operator.tick()
print(operator.contract.blocknumber)
operator.contract.exit(10, 20, 'alice')
operator.contract.challenge_spent_coin(0, 11, 2, '')
