#!/usr/bin/env python
import time, sys

# Monkey-patch affine_equivalence to add instrumentation
from sboxU.ccz import affine_equivalence as ae_module

# Save the original affine_equivalence function
orig_affine = ae_module.affine_equivalence

def instrumented(f, g):
    t0 = time.perf_counter()
    print("Start")
    sf = ae_module.get_sbox(f)
    print("after get_sbox", time.perf_counter()-t0)
    sg = ae_module.get_sbox(g)
    print("after get_sbox2", time.perf_counter()-t0)
    # ... So we need to replicate the logic to measure steps

    # Instead, just call the original
    return orig_affine(f, g)

# But this is messy. Better: edit the cython file to add timing and recompile.