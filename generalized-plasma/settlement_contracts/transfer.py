from utils import Transaction

class TransferTransaction(Transaction):
    def __init__(self, coin_id, plasma_block_number, signer, new_settlement_contract, parameters):
        Transaction.__init__(self, coin_id, plasma_block_number, new_settlement_contract, parameters)
        self.signer = signer

class TransferSettlementContract:
    dispute_duration = 10

    def __init__(self, parent_settlement_contract):
        self.parent = parent_settlement_contract

    def submit_claim(self, claim, witness):
        # Anyone can submit a claim
        return True

    def dispute_claim(self, tx_origin, claim, spend_transaction):
        # Check these are spends of the same coin
        assert claim.transaction.coin_id == spend_transaction.coin_id
        # Check that the signature is valid
        assert claim.transaction.recipient == spend_transaction.signer
        # Check that the spend is after the claim transaction
        assert claim.transaction.plasma_block_number < spend_transaction.plasma_block_number
        return True

    def resolve_claim(self, tx_origin, claim, witness):
        # Check that the resolution is called by the recipient
        assert tx_origin == claim.transaction.recipient
        # Return the recipient who should get the funds
        return claim.transaction.recipient
