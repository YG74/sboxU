#!/usr/bin/env python3
import hashlib
from sboxU.ccz.affine_equivalence.cython_functions import le_class_representative
from sboxU.core import get_sbox

def test_identity():
    # Identity S-box for 8-bit
    s = list(range(256))
    sb = get_sbox(s)
    repr = le_class_representative(sb)
    h = hashlib.md5(bytes(repr.inner_sbox)).hexdigest()
    # Expected checksum from baseline: 14883f789f5ca2090bf3568e5ab34083
    print(f"Identity check: {h}")
    assert h == "14883f789f5ca2090bf3568e5ab34083", f"Checksum mismatch: {h}"
    print("Identity test passed")

if __name__ == "__main__":
    test_identity()