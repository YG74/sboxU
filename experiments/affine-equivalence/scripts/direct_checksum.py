#!/usr/bin/env python
# Directly call benchmark's function

import sys
sys.path.insert(0, '/home/gleb/sboxU')

from benchmark import _import_sboxu, _make_aes_sbox, _checksum

affine_equivalence, get_sbox = _import_sboxu()
aes_raw = _make_aes_sbox()
aes = get_sbox(aes_raw)
result = affine_equivalence.affine_equivalence(aes, aes)
print("Result:", result)
print("Checksum:", _checksum(result))
print("Expected: 14883f789f5ca2090bf3568e5ab34083")

# List items and their types
for i, item in enumerate(result):
    print(f"Item {i}: {type(item).__name__}, has_lut={hasattr(item, 'lut') if hasattr(item, '__class__') else '??'}")
    if hasattr(item, 'lut'):
        print("  LUT:", item.lut()[:10])