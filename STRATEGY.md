# Optimization Strategy — Affine Equivalence Speed

## Current State
- **Best total_time_ms**: 2270.893 (after LTO)
- **Iteration count**: 2

## Bottleneck Analysis
| Benchmark | Value (ms) | % of total | Priority |
|---|---|---|---|
| aes_self | 1928 | 70.8% | HIGH |
| random_nonequiv | 539 | 19.8% | MEDIUM |
| random_self | 254 | 9.3% | LOW |

## Variance Profile
| Benchmark | Median | Std Dev | Noise Band (±2σ) |
|---|---|---|---|
| aes_self | 1928 ms | ~8 ms | ±16 ms |
| random_self | 254 ms | ~3 ms | ±6 ms |
| random_nonequiv | 539 ms | ~7 ms | ±14 ms |

Improvements must exceed 2σ noise band to be considered real.

## Ideas to Try (priority order)

### C++ algorithmic optimizations
1. **Early exit in affine_equivalence_permutations** — The Python loop over all 256 translations could return early once a matching representative is found. Currently, it iterates all 256 before breaking.
2. **Replace dict with hash table** — Replace Python `defaultdict` and `dict.keys()` with C++ `std::unordered_map` to avoid Python overhead.
4. **Pre-check trivial cases** — Check if f(0)=0 and g(0)=0 early to skip translations.
5. **Reduce memory allocations** — In the subroutine, vectors and sets are allocated each call. Pre-allocate or use arena allocators.

### C++ bit-set optimizations
6. **AVX-512 support** — For 256-element sets, AVX-512 could process full sets with single instructions.
7. **Reduce branch mispredictions** — The `shift` function has many conditional branches. Use branchless SIMD consistently.
8. **Inline frequently-used Set operations** — The `shift`, `intersect`, `unite` templates are used heavily — ensure they're always inlined.

### Algorithmic improvements
9. **Caching linear representatives** — Many translations may produce the same linear class representative. Cache results to avoid recomputation.
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

## Exhausted Approaches
(none yet)

## Key Insights
- AES self-equivalence is the dominant bottleneck (~71% of total time) — AES has complex algebraic structure that makes the search harder
- Random permutation self-equivalence is ~7.6x faster than AES — structural properties affect search difficulty
- The C++ subroutine is a backtracking search; pruning and early termination have big impact
- 256-bit AVX2 registers can hold exactly one 8-bit S-box domain (256 bits) — perfectly sized for SIMD
- OpenMP already enabled via compile flags but not used in the linear_representative.cpp code
