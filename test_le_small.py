#!/usr/bin/env python3
import hashlib
from sboxU.ccz.affine_equivalence.cython_functions import le_class_representative
from sboxU.core import get_sbox

def test_identity_4bit():
    s = list(range(16))
    sb = get_sbox(s)
    repr = le_class_representative(sb)
    # access bytes representation
    b = bytes(list(repr))
    h = hashlib.md5(b).hexdigest()
    print(f"4-bit identity checksum: {h}")
    expected = hashlib.md5(bytes(range(16))).hexdigest()
    print(f"expected: {expected}")
    assert h == expected, f"Checksum mismatch: {h} != {expected}"
    print("4-bit identity test passed")

if __name__ == "__main__":
    test_identity_4bit()