from eth_hash.auto import keccak
from web3 import Web3
from eth_utils import (
    int_to_big_endian,
    big_endian_to_int,
)

'''
Transaction format:
list_len + TransferRecord_1 + ... + TransferRecord_n + list_len + Signature_1 + ... + Signature_n

- list_len [4 bytes]: 1 byte describing how many elements in the list, 3 bytes describing the length of each element.
- TransferRecord [152 bytes]: 152 bytes per TransferRecord, up to `x` TransferRecords in each TX.
- Signature [96 bytes]: 96 bytes per signature.

transfer_fields = [
    ('sender', Web3.isAddress),
    ('recipient', Web3.isAddress),
    ('start', is_bytes32_int),
    ('offset', is_bytes32_int),
    ('token_id', is_bytes8_int),
    ('max_block', is_bytes32_int),
    ('nonce', is_bytes8_int),
    ('prime', is_bytes8_int),
]
sig_fields = [
    ('v', is_bytes32_int),
    ('r', is_bytes32_int),
    ('s', is_bytes32_int),
]
'''

def is_bytes32_int(i):
    b = int_to_big_endian(i)
    if len(b) <= 32:
        return True
    else:
        return False

def is_bytes8_int(i):
    b = int_to_big_endian(i)
    if len(b) <= 8:
        return True
    else:
        return False

def get_field_bytes(field):
    if field == Web3.isAddress:
        return 20
    elif field == is_bytes32_int:
        return 32
    elif field == is_bytes8_int:
        return 8
    else:
        raise 'No field type checker recognized'

def get_fields_total_bytes(fields):
    fields_bytes = 0
    for f in fields:
        fields_bytes += get_field_bytes(f[1])
    return fields_bytes

def get_null_tx(start, offset, token_id):
    return TransferRecord(b'\00'*20, b'\00'*20, start, offset, token_id, 0, 0)


class SimpleSerializableElement:
    def __init__(self, *args):
        assert self.fields is not None
        assert len(self.fields) == len(args)
        for i, arg in enumerate(args):
            assert self.fields[i][1]
            setattr(self, self.fields[i][0], arg)

    def encode(self):
        encoding = b''
        for f in self.fields:
            field_type = f[1]
            field_value = getattr(self, f[0])
            if field_type == Web3.isAddress:
                encoding += field_value
            elif field_type == is_bytes32_int:
                encoding += int_to_big_endian(field_value).rjust(32, b'\0')
            elif field_type == is_bytes8_int:
                encoding += int_to_big_endian(field_value).rjust(8, b'\0')
        return encoding

    @classmethod
    def decode(cls, encoding, element_type):
        assert issubclass(element_type, cls)
        assert len(encoding) == get_fields_total_bytes(element_type.fields)
        args = ()
        byte_pos = 0
        for f in element_type.fields:
            field_type = f[1]
            field_bytes_len = get_field_bytes(field_type)
            if field_type == is_bytes8_int or field_type == is_bytes32_int:
                args += (big_endian_to_int(encoding[byte_pos:byte_pos+field_bytes_len]),)
            else:
                args += (encoding[byte_pos:byte_pos+field_bytes_len],)

            byte_pos += field_bytes_len
        return element_type(*args)


class SimpleSerializableList:
    def __init__(self, serializableElements):
        assert len(serializableElements) > 0 and len(serializableElements) < 16
        # Check that all elements are of the same class
        assert all(isinstance(e, type(serializableElements[0])) for e in serializableElements)
        self.serializableElements = serializableElements
        self.field_total_bytes = get_fields_total_bytes(serializableElements[0].fields)

    def encode(self):
        num_elements = int_to_big_endian(len(self.serializableElements))
        element_len = int_to_big_endian(self.field_total_bytes).rjust(3, b'\0')
        header = num_elements + element_len
        encoding = header
        for ele in self.serializableElements:
            encoding += ele.encode()
        return encoding

    @property
    def hash(self) -> bytes:
        return keccak(self.encode())

    @staticmethod
    def decode(encoding, element_type):
        num_elements = encoding[0]
        element_len = big_endian_to_int(encoding[1:4])
        elements = []
        for i in range(num_elements):
            start_pos = 4 + i*element_len
            end_pos = start_pos+element_len
            elements.append(SimpleSerializableElement.decode(encoding[start_pos:end_pos], element_type))
        return elements


class TransferRecord(SimpleSerializableElement):
    fields = [
        ('sender', Web3.isAddress),
        ('recipient', Web3.isAddress),
        ('start', is_bytes32_int),
        ('offset', is_bytes32_int),
        ('token_id', is_bytes8_int),
        ('max_block', is_bytes32_int),
        ('nonce', is_bytes8_int),
        ('prime', is_bytes8_int),
    ]

    @property
    def hash(self) -> bytes:
        return keccak(self.encode())


class Signature(SimpleSerializableElement):
    fields = [
        ('v', is_bytes32_int),
        ('r', is_bytes32_int),
        ('s', is_bytes32_int),
    ]


class DepositRecord(SimpleSerializableElement):
    fields = [
        ('recipient', Web3.isAddress),
        ('amount', is_bytes32_int),
        ('token_id', is_bytes8_int),
    ]
