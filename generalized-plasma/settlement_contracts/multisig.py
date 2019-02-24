from utils import Transaction

class MultiSigTransaction(Transaction):
    def __init__(self, coin_id, plasma_block_number, signers, new_settlement_contract, parameters):
        Transaction.__init__(self, coin_id, plasma_block_number, new_settlement_contract, parameters)
        self.signers = signers  # Array of owner's signatures (in this it is just their names)

class MultiSigSettlementContract:
    dispute_duration = 10

    def __init__(self, parent_settlement_contract):
        self.parent = parent_settlement_contract

    def submit_claim(self, claim, witness):
        # Anyone can submit a claim
        return True

    def dispute_claim(self, tx_origin, claim, spend_transaction):
        # Check these are spends of the same coin
        assert claim.transaction.coin_id == spend_transaction.coin_id
        # Check that the settlement contract of the claim is this contract
        assert claim.transaction.new_settlement_contract == self
        # Check that all signers have signed
        assert claim.transaction.recipient == spend_transaction.signers
        # Check that the spend is after the claim transaction
        assert claim.transaction.plasma_block_number < spend_transaction.plasma_block_number
        return True

    def resolve_claim(self, tx_origin, claim, witness):
        # Extract required information from witness
        recipients_sigs, destination = witness
        # Check that the resolution is signed off on by all parties in the multisig
        assert recipients_sigs == claim.transaction.recipient
        # Return the recipient who should get the funds
        return destination
