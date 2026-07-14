#!/usr/bin/env python
"""Regression test for affine equivalence of non-identical permutations.

Background
----------
``affine_equivalence`` returned an empty list for genuinely affine-equivalent
permutations that were not identical. The self-equivalence fast path masked the
bug, and the existing benchmark only exercised self-equivalence and
non-equivalent pairs.

Root cause
----------
``cpp_differential_spectrum_compare`` (sboxU/cpp/statistics/differential.cpp)
compared DDT histograms after every input-difference row and exited early on
any mismatch. For affine-equivalent functions the DDT rows are permuted by the
linear maps, so intermediate cumulative histograms differ even though the final
differential spectra are identical.

This test exercises the public ``affine_equivalence`` seam for 6-bit and 8-bit
permutations, both for a random affine-equivalent pair and for a negative pair.
"""

import sys
import random

from sboxU import get_sbox, affine_equivalence
from sboxU.random_objects import rand_linear_permutation, rand_invertible_Sbox


SEED = 42


def make_affine_equivalent(f, n, rng):
    """Return g = A o f o B with affine constants a, b.

    g(x) = A(f(B(x ^ a))) ^ b, so g and f are affine equivalent.
    """
    A = rand_linear_permutation(n).get_S_box()
    B = rand_linear_permutation(n).get_S_box()
    a = rng.randint(0, (1 << n) - 1)
    b = rng.randint(0, (1 << n) - 1)
    g = A * f * B
    return get_sbox([g.lut()[x ^ a] ^ b for x in range(1 << n)])


def check_positive(n, rng, label):
    f = rand_invertible_Sbox(n)
    g = make_affine_equivalent(f, n, rng)
    mappings = affine_equivalence(f, g)
    if len(mappings) == 0:
        print(
            f"[FAIL] {label}: affine_equivalence returned no mapping for an affine-equivalent pair"
        )
        return False
    print(f"[ OK ] {label}: found {len(mappings) // 4} affine mapping(s)")
    return True


def check_negative(n, label):
    f = rand_invertible_Sbox(n)
    h = rand_invertible_Sbox(n)
    mappings = affine_equivalence(f, h)
    if len(mappings) != 0:
        print(
            f"[FAIL] {label}: affine_equivalence returned mapping(s) for a random non-equivalent pair"
        )
        return False
    print(f"[ OK ] {label}: random non-equivalent pair correctly rejected")
    return True


def main():
    rng = random.Random(SEED)
    failures = 0
    # 6-bit and 8-bit are fast enough for a regression harness;
    # 12-bit affine equivalence is correct but too slow for routine CI.
    for n in (6, 8):
        if not check_positive(n, rng, f"affine-equivalent {n}-bit"):
            failures += 1
        if not check_negative(n, f"non-equivalent {n}-bit"):
            failures += 1

    if failures:
        print(f"\n{failures} check(s) failed")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
