import rlp
from rlp.sedes import big_endian_int, List, CountableList
from eth_hash.auto import keccak
from eth.rlp.sedes import address

tx_fields = [
    ('sender', address),
    ('recipient', address),
    ('start', big_endian_int),
    ('offset', big_endian_int),
    ('token_id', big_endian_int),
    ('parent_start', big_endian_int),
]
sig_fields = [
    ('v', big_endian_int),
    ('r', big_endian_int),
    ('s', big_endian_int),
]


class Transaction(rlp.Serializable):
    fields = tx_fields

    @property
    def hash(self) -> bytes:
        return keccak(rlp.encode(self))


class Signature(rlp.Serializable):
    fields = sig_fields


class MultiTx(rlp.Serializable):
    fields = [
        ('transactions', CountableList(List([f[1] for f in tx_fields]), 9)),
        ('signatures', CountableList(List([f[1] for f in sig_fields]), 9)),
    ]

    @property
    def hash(self) -> bytes:
        return keccak(rlp.encode(self))
