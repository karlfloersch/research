from contract import PlasmaContract

contract = PlasmaContract()
contract.deposit('test', 100, '0xme')
print(contract.total_deposits)
contract.add_block('0xblockhash-test')
print(contract.blocks)
