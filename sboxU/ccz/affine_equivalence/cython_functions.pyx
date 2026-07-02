# -*- python -*-

from libcpp.vector cimport vector

from sboxU.core import get_sbox, oplus
from sboxU.core.sbox import F2_trans
from sboxU.config import MAX_N_THREADS
from collections import defaultdict
from sboxU.statistics import differential_spectrum, early_differential_spectrum_compare
from sboxU.core.f2functions import identity_F2AffineMap


from cython.operator cimport dereference


# !SECTION! XOR equivalence

def xor_equivalence(s, s_prime, all_pairs=True):
    sb, sb_prime = get_sbox(s), get_sbox(s_prime)
    if sb.get_input_length() != s_prime.get_input_length():
        return []
    else:
        result = []
        for a in sb.input_space():
            offset = oplus(sb[a], sb_prime[0])
            valid_pair = True
            for x in sb.input_space():
                if (s[oplus(x, a)] != oplus(offset, sb_prime[x])):
                    valid_pair = False
                    break
            if valid_pair:
                result.append([a, offset])
                if not all_pairs:
                    return result
        return result
        

# !SECTION! Linear equivalence

def le_class_representative(s):
    """Computes the smallest member of the linear-equivalence class of the S_boxable object `s`.

    It is assumed that `s` corresponds to a permutation since this function relies on the algorithm presented in [EC:BDCBP03]. A dedicated implementation for the case where s.get_input_length() is at most 8 enables a very computation in this case. Otherwise, defaults to a much slower implementation.

    Args:
        - s: an S_boxable object.

    Returns:
        An `S_box` instance corresponding to the smallest function in the linear equivalence class of `s`, where "smallest" is in the sense of the lexicographic order.
    
    """
    sb = get_sbox(s)
    if sb.is_invertible():
        result = S_box(name=b"LE(" + sb.name() + b")")
        result.set_inner_sbox(
            # we always try use the "fast" variant of cpp_le_class_representative
            cpp_le_class_representative(dereference((<S_box>sb).cpp_sb))
        )
        return result
    else:
        raise NotImplementedError("Linear representatives can only be computed for permutations")




def compute_all_le_reps_parallel(list sbox_list):
    """Compute linear class representatives for a list of S_boxes in parallel.
    Returns a list of S_box objects.
    """
    cdef vector[cpp_S_box] cpp_sboxes
    cpp_sboxes.reserve(len(sbox_list))
    cdef S_box sb
    for sb in sbox_list:
        cpp_sboxes.push_back(dereference((<S_box>sb).cpp_sb))

    cdef vector[cpp_S_box] reps = parallel_compute_le_class_representatives(cpp_sboxes)

    results = []
    cdef S_box new_sb
    cdef cpp_S_box rep
    for rep in reps:
        new_sb = S_box()
        new_sb.set_inner_sbox(rep)
        results.append(new_sb)
    return results


def linear_equivalence(f, g, all_mappings=False):
    sf = get_sbox(f)
    sg = get_sbox(g)
    if len(f) != len(g):
        raise ValueError("f and g are of different dimensions!")
    if sf.is_invertible() or sg.is_invertible():
        if sf.is_invertible() and sg.is_invertible():
            return linear_equivalence_permutations(sf, sg, all_mappings=all_mappings)
        else:
            return False # a permutation can only be linear equivalent
                         # to another permutation
    else:
        # !TODO! use Jules table-based algorithm or Itai's algorithm if the degree is maximum
        raise NotImplementedError("only permutations are implemented at the moment")
    


def linear_equivalence_permutations(f, g, all_mappings=False):
    """Returns, if it exists, the tuple A, a, B, b where A and B are matrices such that, for all x:

    f = B o g o A

    where "o" denotes functional composition. If no such linear permutations exist, returns an empty list.

    The algorithm used is specified in [EC:BDCBP03].

    """
    sf = get_sbox(f)
    sg = get_sbox(g)
    result = cpp_linear_equivalence_permutations(
        dereference((<S_box>sf).cpp_sb),
        dereference((<S_box>sg).cpp_sb),
        all_mappings
        )
    mappings = []
    for cpp_A in result:
        A = F2AffineMap()
        A.set_inner_map(<cpp_F2AffineMap>cpp_A)
        mappings.append(A)
    return [(mappings[i], mappings[i+1])
            for i in range(0, len(mappings), 2)]
    
    


# !SECTION! Affine equivalence



def affine_equivalence(f, g):
    sf = get_sbox(f)
    sg = get_sbox(g)
    if len(f) != len(g):
        raise ValueError("f and g are of different dimensions!")
    if sf.is_invertible() or sg.is_invertible():
        if sf.is_invertible() and sg.is_invertible():
            return affine_equivalence_permutations(sf, sg)
        else:
            return False # a permutation can only be affine equivalent
                         # to another permutation
    else:
        # !TODO! use Jules table-based algorithm in general, and Alain's algorithm for quadratic functions
        raise NotImplementedError("only permutations are implemented at the moment")
    

def affine_equivalence_permutations(f, g):
    """Returns, if it exists, the tuple A, a, B, b where A and B are
    matrices and where a and b are integers such that, for all x:

    f(x) = (B o g o A)(x + a) + b,

    where "o" denotes functional composition and "+" denotes XOR. If
    no such affine permutations exist, returns an empty list.

    Internally calls a function written in C++ for speed which returns
    the "Linear Representative" using an algorithm from [EC:BDCBP03].

    """

    sf = get_sbox(f)
    sg = get_sbox(g)

    if len(f) != len(g):
        raise ValueError("f and g are of different dimensions!")
    if not sf.is_invertible():
        raise Exception("first argument is not a permutation!")
    if not sg.is_invertible():
        raise Exception("second argument is not a permutation!")

    # Fast path for self-equivalence: f == g => identity mapping is a solution
    if sf == sg:
        n = sf.get_input_length()
        identity_A = identity_F2AffineMap(n)
        identity_B = identity_F2AffineMap(n)
        return [identity_A, 0, identity_B, 0]

    # Quick filter: differential spectrum is an affine invariant for permutations
    # If the differential spectra differ, f and g cannot be affine equivalent.
    # This avoids running the expensive full algorithm for most non-equivalent pairs.
    try:
        if not early_differential_spectrum_compare(sf, sg):
            return []
    except Exception:
        # If early_differential_spectrum_compare fails for any reason, fall back to full algorithm
        pass
    # Setup translations
    n = sf.get_input_length()
    tr = [F2_trans(c, bit_length=n) for c in sf.input_space()]

    # Incremental hash table with early exit
    table_f = defaultdict(int)  # rep -> c for f
    table_g = defaultdict(int)  # rep -> c for g
    a = -1
    b = -1
    rs = []
    for c in sf.input_space():
        f_c = tr[c] * sf
        g_c = sg * tr[c]
        f_rep = le_class_representative(f_c)
        g_rep = le_class_representative(g_c)
        # Add f_rep to its table and check if g_rep matches any f_rep
        table_f[f_rep] = c
        if g_rep in table_f:
            a = c
            b = table_f[g_rep]
            rs = g_rep
            break
        # Add g_rep to its table and check if f_rep matches any g_rep
        table_g[g_rep] = c
        if f_rep in table_g:
            a = table_g[f_rep]
            b = c
            rs = f_rep
            break
    if a == -1:
        return []
    # !FINISH! 
    l_f = linear_equivalence(tr[b] * sf, rs)
    A_f, B_f = l_f[0][0], l_f[0][1]
    l_g = linear_equivalence(sg * tr[a], rs)
    A_g, B_g = l_g[0][0], l_g[0][1]
    A = A_g.inverse() * A_f
    B = B_f *B_g.inverse()
    a = A.inverse()(a)
    return [A, a, B, b]
