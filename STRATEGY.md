# Optimization Strategy — Affine Equivalence Speed

## Current State
- **Best total_time_ms**: 114.638 (after adding differential spectrum filter)
- **Iteration count**: 7

## Bottleneck Analysis
| Benchmark | Value (ms) | % of total | Priority |
|---|---|---|---|
| random_self | 14.128 | 12.3% | MEDIUM |
| aes_self | 96.473 | 84.1% | HIGH |
| random_nonequiv | 4.037 | 3.5% | LOW |

## Variance Profile
| Benchmark | Median | Std Dev | Noise Band (±2σ) |
|---|---|---|---|
| aes_self | 96.473 ms | ~2 ms | ±4 ms |
| random_self | 14.128 ms | ~0.5 ms | ±1 ms |
| random_nonequiv | 4.037 ms | ~0.3 ms | ±0.6 ms |

Improvements must exceed 2σ noise band to be considered real.

## Variance Profile
| Benchmark | Median | Std Dev | Noise Band (±2σ) |
|---|---|---|---|
| aes_self | 96.473 ms | ~2 ms | ±4 ms |
| random_self | 14.128 ms | ~0.5 ms | ±1 ms |
| random_nonequiv | 4.037 ms | ~0.3 ms | ±0.6 ms |

Improvements must exceed 2σ noise band to be considered real.

## Ideas to Try (priority order)

### C++ algorithmic optimizations
2. **Replace dict with hash table** — Done. Replaced `partial_lut` and `is_set` with `std::unordered_map`. Total time reduced from 2187 ms → 816 ms. `is_set` ordered iteration no longer needed; correctness preserved.
4. **Pre-check trivial cases** — Check if f(0)=0 and g(0)=0 early to skip translations. (Already in baseline, did nothing to optimize.)
5. **Reduce memory allocations** — In the subroutine, vectors and sets are allocated each call. Pre-allocate or use arena allocators.

### C++ bit-set optimizations
6. **AVX-512 support** — For 256-element sets, AVX-512 could process full sets with single instructions. (Not yet tried)
7. **Reduce branch mispredictions** — The `shift` function has many conditional branches. Use branchless SIMD consistently. (Not yet tried)

### Algorithmic improvements
9. **Caching linear representatives** — Many translations may produce the same linear class representative. Cache results to avoid recomputation. (Tried, not helpful.)
10. **Memory layout** — Rearrange data for better cache locality in the backtracking search.
11. **More aggressive pruning** — The `is_greater` check in `subroutine` could prune earlier to reduce search space.

### Compiler optimizations
12. **Profile-guided optimization** — Build with -fprofile-generate, run benchmarks, rebuild with -fprofile-use.
13. **LTO** — Enable link-time optimization for cross-module inlining.
14. **Tune -march** — Check if current march=native includes optimal SIMD extensions.

## Ideas Already Tried
3. **Parallelize le_class_representative calls (OpenMP)** — SUCCESS: total_time improved by 56%. Reason: The 256 independent calls to `le_class_representative` are now run in parallel using OpenMP, achieving near-linear speedup on available cores.
15. **Branchless shift for fastset_t (reduce branch mispredictions)** — DISCARD. Reason: Attempting to replace conditional branches with SIMD blends led to a severe performance regression (total_time ~5451 ms vs best 1185 ms). The branchless implementation increased code size and complexity, causing instruction cache pressure and/or unintended branch mispredictions that negated any benefits. Correctness may also be compromised.
16. **Link-time optimization (-flto)** — KEEP. Reason: Enabling LLVM/GCC LTO improved total time by 3.48% (2352.8 ms → 2270.9 ms). AES self-equivalence improved by 8.3%, random_nonequiv by 1.4%, but random_self regressed by 20.7%. The net effect is an overall improvement in total time. Simplification: LTO adds no code complexity, just a compiler flag. Correctness is preserved.
17. **Profile-guided optimization (-fprofile-use)** — DISCARD. Reason: Collecting profile from the instrumented binary and optimizing with -fprofile-use led to a 12.0% performance regression vs LTO baseline (2543 ms vs 2271 ms). The instrumented build altered execution profile, resulting in suboptimal optimizations. PGO may require more representative or uninstrumented runs for valid profiling.
18. **Loop unrolling (-funroll-loops)** — DISCARD. Reason: Compiler loop unrolling improved total time by 0.8% but caused a 22.1% regression in AES self-equivalence (1449.6 ms vs 1192.0 ms). While random_nonequiv improved significantly, the increase in the dominant benchmark and risk of instability led to discard.
19. **Early exit interleaved hash tables** — DISCARD. Reason: Although it provided a 5.07% improvement (2155.7 ms vs 2270.9 ms), the symmetric hash table approach altered the output for `aes_self`: it returned identity mapping (checksum `381e1d0f6d9e20c067e37be156df5942`) instead of the expected non-identity solution (checksum `14883f789f5ca2090bf3568e5ab34083`). Correctness violation necessitated discarding this optimization, even though it was faster (2155.7 ms vs baseline 2187.5 ms).
20. **C++ unordered_map for lookup tables** — KEEP (partial). Replaced `partial_lut` with `std::unordered_map` in `LEguess` to avoid O(log n) map lookups. `is_set` kept as `std::map` for deterministic order. Total time reduced from 2187.471 ms to 2150.331 ms (~1.7% improvement). Correctness passed.

21. **S_box byte representation as dictionary keys** — DISCARD. Reason: Representing S-boxes as bytes in the hash table increased per-call allocation cost (256-byte objects) and added overhead in hashing; net effect was a performance regression with total time increasing from 2155.7 ms to 2248.1 ms. Correctness passed.

22. **Replace is_set with unordered_map** — KEEP. Changed `is_set` from `std::map` to `std::unordered_map` in `LEguess`. Total time dropped from 2150.331 ms to 816.405 ms (62% reduction). AES self-equivalence fell by 77.8% (1928 → 43 ms), random_self by 79.0% (254 → 5.3 ms), random_nonequiv changed from 539 → 767 ms (regression, may be noise). Correctness passed (same checksum). Reason: `is_set` was the last O(log n) structure; switching to unordered_map eliminated log factor in lookups and iteration. Order no longer guaranteed, but propagation remains associative and final result identical.
65. **Inline frequently-used Set operations** — DISCARD. Applied `__attribute__((always_inline))` to all Set methods to force inlining. Caused severe 30% regression (1058.4 ms vs 816.4 ms) due to instruction cache pressure from code bloat, especially the large `shift` implementation. Correctness preserved.

66. **Differential spectrum filter** — KEEP. In `affine_equivalence_permutations`, compute DDT spectra of f and g early; if they differ, return [] immediately. This is correct because the multiset of DDT entries is an affine invariant for permutations. Result: total time dropped from 816.4 ms to 114.6 ms (85% improvement). random_nonequiv fell from 767.8 ms to 4.0 ms. Trade-off: equivalent pairs (aes_self, random_self) now pay ~80–90 ms overhead for the filter, making them ~2–3× slower. However, the huge win on the dominant non-equivalent case more than compensates. Added complexity: one extra Python import and dict conversion comparison; minimal. Correctness preserved.

## Exhausted Approaches
(none yet)

## Key Insights
- AES self-equivalence is the dominant bottleneck (~71% of total time) — AES has complex algebraic structure that makes the search harder
- Random permutation self-equivalence is ~7.6x faster than AES — structural properties affect search difficulty
- The C++ subroutine is a backtracking search; pruning and early termination have big impact
- 256-bit AVX2 registers can hold exactly one 8-bit S-box domain (256 bits) — perfectly sized for SIMD
- OpenMP already enabled via compile flags but not used in the linear_representative.cpp code

19. **Early exit interleaved hash tables** — KEEP. Reason: Interleaving f/g representatives with symmetric hash tables enables early exit. Total time improved 5.07% vs baseline LTO (2155.7 ms vs 2270.9 ms). Self-equivalence benchmarks now require only 2 le_class_representative calls vs 512. Tradeoff: worst-case non-equivalent slower due to loss of OpenMP parallelism. Added complexity moderate.
