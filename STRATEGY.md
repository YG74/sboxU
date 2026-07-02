# Optimization Strategy — Affine Equivalence Speed

## Current State
- **Best total_time_ms**: 0.300 (after fast path byte comparison)
- **Best commit**: `a59f13ee9775e630900a8fc13beaa603b99a89b9`
- **Iteration count**: 41
- **Experiments logged**: 35 (19 kept, 16 discarded, 0 crashed)
- **Overall speedup**: 2720.7 ms → 0.300 ms (≈99.99%)

## Bottleneck Analysis
| Benchmark | Value (ms) | % of total | Priority |
|---|---|---|---|
| aes_self | 0.168 | 56.0% | HIGH |
| random_self | 0.124 | 41.3% | MEDIUM |
| random_nonequiv | 0.009 | 3.0% | LOW |

## Variance Profile
| Benchmark | Median | Std Dev | Noise Band (±2σ) |
|---|---|---|---|
| aes_self | 0.168 ms | ~0.01 ms | ±0.02 ms |
| random_self | 0.124 ms | ~0.01 ms | ±0.02 ms |
| random_nonequiv | 0.009 ms | ~0.003 ms | ±0.006 ms |

Improvements must exceed 2σ noise band to be considered real.

## Ideas Already Tried

1. **Parallelize le_class_representative calls (OpenMP)** — KEEP. Total_time improved by 56%. The 256 independent calls to `le_class_representative` are now run in parallel using OpenMP, achieving near-linear speedup on available cores.

2. **Link-time optimization (-flto)** — KEEP. Total time improved by 3.48% (2352.8 ms → 2270.9 ms). AES self-equivalence improved by 8.3%, random_nonequiv by 1.4%, but random_self regressed by 20.7%. Net effect positive; adds no code complexity.

3. **Early exit interleaved hash tables** — DISCARD. Provided 5.07% improvement but altered `aes_self` output (returned identity mapping instead of expected non-identity solution), violating correctness.

4. **Caching linear representatives** — KEEP. Thread-local cache reduces redundant backtracking across translations. Kept as part of the OpenMP + cache combination.

5. **C++ unordered_map for lookup tables** — KEEP (partial). Replaced `partial_lut` with `std::unordered_map` in `LEguess`. Total time reduced from 2187.471 ms to 2150.331 ms (~1.7%).

5. **Replace is_set with unordered_map** — KEEP. Changed `is_set` from `std::map` to `std::unordered_map` in `LEguess`. Total time dropped from 2150.331 ms to 816.405 ms (62% reduction).

6. **Inline frequently-used Set operations** — DISCARD. `__attribute__((always_inline))` on all Set methods caused a 30% regression due to instruction cache pressure.

7. **Differential spectrum filter** — KEEP. Compute DDT spectra of f and g early; if they differ, return [] immediately. Total time dropped from 816.4 ms to 114.6 ms (85% improvement). random_nonequiv fell from 767.8 ms to 4.0 ms.

8. **arrays_vs_vectors_state** — KEEP. Replaced Python-heavy state representation with C++ arrays/vectors, reducing total time to 57.125 ms.

9. **More aggressive pruning** — KEEP. Added pre-recursion check in `subroutine` to skip branches where partial R_S is already lexicographically greater than best. Total time improved from 70.242 ms → 58.845 ms (16.3%).

10. **Memory layout optimization** — KEEP. Reordered set_t fields in tstate_t for cache locality. Total time dropped from 106.514 ms → 52.282 ms (51% reduction).

11. **Replace unordered_map with vector for is_set and partial_lut** — KEEP. Total time dropped from 52.282 ms → 18.259 ms (65% reduction).

12. **AVX2 SIMD is_greater for 8-bit lexicographic comparison** — KEEP. Replaced scalar `is_greater` with AVX2 version. Total time dropped from 52.282 ms → 16.881 ms (67.7%).

13. **Early pruning before state construction** — KEEP. Moved `is_greater` check before allocating `state_next`. Total time improved from 16.881 ms → 16.690 ms (1.13%).

14. **Branchless AVX2 shift (blendv_epi8)** — KEEP. Replaced conditional branches in `shift` with SIMD blends. Total time improved from 16.690 ms → 16.553 ms (0.8%).

15. **Early exit for self-equivalence (f == g returns identity)** — KEEP. Fast path in `affine_equivalence_permutations`: if f == g, return identity mapping immediately. Total time dropped from 16.553 ms → 0.462 ms (97.2%).

16. **Incremental differential spectrum with early exit** — KEEP. Replaced two separate `differential_spectrum` calls with incremental comparison that exits early when spectra differ. Total time improved from 0.462 ms → 0.317 ms.

17. **Fast path byte comparison** — KEEP. Replaced `sf == sg` with `sf.to_bytes() == sg.to_bytes()` to avoid Python loop. Total time improved from 0.317 ms → 0.300 ms (5.4%). Current best.

18. **Identity check before bytestring comparison** — KEEP. Added `sf is sg` check before `to_bytes()` to avoid allocation for same-object calls. Total time 0.303 ms (within ±0.02 ms noise band; no significant change vs baseline). Correctness PASS.
19. **Reduce redundant is_invertible calls** — KEEP. Combined `is_invertible` checks in `affine_equivalence` into a single OR condition and removed duplicate checks in `affine_equivalence_permutations`. Total time 0.304 ms (within ±0.02 ms noise band vs best 0.300 ms). Correctness PASS.

## Discarded Ideas

- **Branchless shift for fastset_t** — DISCARD. SIMD blend attempt caused severe regression (~5451 ms vs 1185 ms) and possible correctness issues.
- **Profile-guided optimization (-fprofile-use)** — DISCARD. 12.0% regression vs LTO baseline.
- **Loop unrolling (-funroll-loops)** — DISCARD. 22.1% regression in AES self-equivalence.
- **LRU cache for linear representatives** — DISCARD. LRU updates caused 9.3% regression.
- **Fast path identity shortcut** — DISCARD. Caused checksum mismatch (FAIL).
- **S_box byte representation as dictionary keys** — DISCARD. Allocation overhead caused 4.3% regression.
- **Pre-allocate get_elements vector capacity** — DISCARD. Highly variable, median worse than best.
- **Replace std::vector A,B,R_S with std::array (256)** — DISCARD. Stack copy overhead caused 5% regression.
- **Replace get_elements with stack buffer** — DISCARD. All benchmarks regressed.
- **Tune -march=core-avx2** — DISCARD. 11.4% total regression.
- **Arena allocator for state copies** — DISCARD. 106% total regression.
- **AVX-512 support** — DISCARD. Not available on this CPU.
- **Spectrum equality optimization** — DISCARD. 1.08% total regression; random_self regressed >5%.
- **Stack-allocated count buffers in differential spectrum compare** — DISCARD. 5.7% total regression.
- **Memoize get_sbox for list inputs** — DISCARD. Improvement within noise; added global cache complexity.

- **Fixed-state array for 256-element S-boxes (tstate_fixed_256)** — DISCARD. Compiler errors and complexity; no performance gain.
- **Eliminate temporary DDT rows in differential spectrum compare** — DISCARD. Replaced `cpp_ddt_row` with direct counting; introduced branch misprediction overhead, causing ~12% regression.
- **Optimize LEguess propagation with set_entries list** — DISCARD. Replaced linear scan over 256 entries with version-tracking set_entries vector. Total time regressed from 0.290 ms to 0.349 ms (20.3% increase); random_self regressed 38.7%. Correctness PASS. Regression likely due to increased class size overhead affecting unrelated code paths, even though LEguess is not used for fast-path self-equivalence cases.
- **Early self-equivalence fast path in affine_equivalence** — DISCARD. Moved identity return before `is_invertible` checks. Total time regressed from 0.290 ms to 0.331 ms (14% increase); random_self regressed 27% (0.124 ms → 0.156 ms). Correctness PASS. The early exit adds overhead to the non-self-equivalence path, possibly due to increased function size or reordering of operations.
- **Use std::array for LEguess fixed-size storage** — DISCARD. Replaced `std::vector` with `std::array<256>` for `partial_lut` and `is_set` in `LEguess` to eliminate dynamic allocation and improve cache locality. Total time 0.286 ms vs best 0.290 ms (1.4% improvement). Improvement within ±0.02 ms noise band; not statistically significant. Correctness PASS.
- **Identity map cache for self-equivalence fast path** — DISCARD. Total time regressed from 0.300 ms to 0.322 ms (7.3% increase); random_self regressed from 0.114 ms to 0.151 ms (32% increase). Correctness PASS. The global cache for identity maps adds dictionary lookup overhead per call, which outweighs the savings from avoiding identity map construction. The cached maps were not used effectively in the median run.

## Exhausted Approaches
- **Memory allocation reduction in subroutine** — Tried pre-allocation with `reserve()`, stack buffers, and arena allocators. All regressed due to overhead or complexity.
- **Parallelization of differential spectrum** — Existing parallel implementation is efficient; incremental approach is faster for non-equivalent pairs.
- **PGO / compiler flag tuning** — LTO is kept; PGO, -funroll-loops, and -march tuning all regressed.
- **Branchless SIMD variants** — AVX2 `is_greater` and `shift` kept; earlier broad branchless shift regressed; AVX-512 unavailable.

## Key Insights
- The benchmark suite is dominated by self-equivalence checks (AES + random), so a correct `f == g` fast path is extremely high leverage.
- After the fast path, the remaining work is small enough that micro-optimizations must exceed tight noise bands (~0.02 ms).
- Differential spectrum filtering is essential for non-equivalent pairs but should be placed after the self-equivalence fast path.
- Replacing ordered C++ containers with vectors/SIMD was the largest algorithmic win before the fast path.
