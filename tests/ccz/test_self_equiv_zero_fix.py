#!/usr/bin/env python
"""Regression test for the F(0)=0 self-equivalence bug.

Background
----------
``sboxU.self_linear_equivalent_mappings`` returned *zero* linear
self-equivalences for every permutation that fixes 0 (``F(0) == 0``),
including the identity permutation, even though the identity trivially
admits the identity self-equivalence.

Root cause
----------
``LEguess::LEguess`` (sboxU/cpp/ccz/linear_equivalence.cpp) pre-set
``is_set[0] = 1`` (``B(0) = 0`` is forced for any linear permutation B)
but left ``min_unset = 0`` instead of advancing it past the fixed entry.
In the ``F(0) == 0`` branch of ``cpp_linear_equivalence_permutations`` the
``constraints`` vector stays empty, so ``LEguessIterator`` seeded its first
guess on the already-fixed entry 0 and every candidate ``y`` immediately
threw ``ContradictionFound`` -> the search reported no self-equivalences.

The fix advancing ``min_unset`` past entry 0 in the constructor makes the
iterator target the first genuinely unset entry, and the propagation
re-seeds correctly.

This test exercises the real call path ``self_linear_equivalent_mappings``
for permutations that fix 0 (the bug path) and asserts (a) at least one
mapping is returned, and (b) every returned pair ``(A, B)`` satisfies
``B . S . A == S`` exactly over the whole input space.
"""

import sys
from sage.all import GF, Matrix, vector

from sboxU import (
    get_sbox,
    self_linear_equivalent_mappings,
    S_box,
)


def identity_sbox(n):
    """Identity permutation over (F_2)^n. Fixes 0 by construction."""
    return get_sbox(list(range(1 << n)))


def bit_rotation_sbox(n, shift):
    """Cyclic bit-rotation by ``shift`` positions; fixes 0 by construction.

    A non-trivial example of a permutation with F(0)=0 and a known large
    self-equivalence group (it commutes with every cyclic shift of the same
    rotation, and the rotation matrix itself is a linear automorphism).
    """
    N = 1 << n
    out = [((x << shift) | (x >> (n - shift))) & (N - 1) for x in range(N)]
    return get_sbox(out)


def check_mappings(S, label):
    mappings = self_linear_equivalent_mappings(S)
    if not mappings:
        print(f"[FAIL] {label}: self_linear_equivalent_mappings returned 0 mappings")
        return False
    # Verify each (A, B) satisfies B(S(A(x))) == S(x) for all x.
    ok = True
    for i, (A, B) in enumerate(mappings):
        A_lut = A.get_S_box()
        B_lut = B.get_S_box() if hasattr(B, "get_S_box") else B.get_S_box()
        # Compose: A(S^{-1}(x)) ?? — the library convention here is
        # elt[0] is A and elt[1] is B, with B o S o A == S.
        # We check directly: for every x, B_lut[ S_lut[ A_lut[x] ] ] == S_lut[x].
        S_lut = [S[x] for x in range(len(S))]
        if any(B_lut[S_lut[A_lut[x]]] != S_lut[x] for x in range(len(S))):
            print(f"[FAIL] {label}: mapping #{i} does not satisfy B o S o A == S")
            ok = False
    if ok:
        print(f"[ OK ] {label}: {len(mappings)} mappings, all verify B o S o A == S")
    return ok


def main():
    failures = 0
    # Sizes where the linear self-equivalence search is cheap enough to run
    # under all_mappings=True in a regression harness.
    for n in (2, 3, 4):
        if not check_mappings(identity_sbox(n), f"identity n={n} (F(0)=0)"):
            failures += 1
        # Cyclic bit rotation; even shift modulo n.
        shift = 1
        if shift % n != 0:
            if not check_mappings(
                bit_rotation_sbox(n, shift), f"bit_rot n={n} shift={shift} (F(0)=0)"
            ):
                failures += 1
    # Sanity: a permutation with F(0)!=0 continues to work (guard against
    # accidentally breaking the F(0)!=0 path while fixing the F(0)=0 path).
    shifted_id = get_sbox(list(range(1, 8)) + [0])
    r = self_linear_equivalent_mappings(shifted_id)
    if len(r) == 0:
        print("[FAIL] shifted identity n=3 (F(0)!=0) returned 0 mappings")
        failures += 1
    else:
        print(f"[ OK ] shifted identity n=3 (F(0)!=0): {len(r)} mappings")

    if failures:
        print(f"\n{failures} check(s) failed")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
