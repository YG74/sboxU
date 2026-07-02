# sboxU Auto-Research Program — Affine Equivalence Speed

You are an autonomous optimization agent for **sboxU** (S-box utility library).
Your goal: **make the affine equivalence check (Biryukov algorithm) faster** without breaking correctness.

## Background

The affine equivalence check finds matrices A, B and vectors a, b such that:

    f(x) = (B ∘ g ∘ A)(x + a) + b   for all x

The algorithm (Bir06 / BDCBP03):
1. Computes linear class representatives for all 2^n translations of f
2. Builds a hash table matching representatives between f and g
3. Computes linear equivalences for matched representatives
4. Derives affine transformation parameters

The heavy computation is in C++ (cpp/ccz/linear_representative.cpp):
- Backtracking search with bit-set operations using AVX2/NEON SIMD
- OpenMP parallelization available via compile flags

## Environment
- **Project**: /home/gleb/sboxU
- **Benchmark**: benchmark.py — fixed, DO NOT MODIFY
- **Baseline**: baseline_checksums.json — DO NOT MODIFY
- **Results**: results.tsv — experiment log (append-only)
- **Strategy**: STRATEGY.md — what to try next
- **Build**: `pip install -e .` from project root (Cython → C++ compilation)
- **Runtime**: `sage -python` (required for SageMath Cython deps)

## One Iteration = One Experiment

### Step 1: Read State
Read `results.tsv` and `STRATEGY.md` to know where you are.

### Step 2: Decide What to Try
- Pick ONE idea from STRATEGY.md
- Prefer high-impact ideas targeting the biggest bottleneck
- Start simple, escalate only if simple ideas are exhausted
- If all ideas exhausted, analyze code for new ones

### Step 3: Implement
- Keep changes small and focused — one idea per experiment
- **CAN modify**: any file in sboxU/ (Python, Cython .pyx, C++ .cpp/.h)
- **CANNOT modify**: benchmark.py, baseline_checksums.json, run_agr.sh, analysis.py, STRATEGY.md formatting
- After changing C++/Cython code, rebuild with `pip install -e .`

### Step 4: Build (if needed)
```bash
cd /home/gleb/sboxU
pip install -e . 2>&1 | tail -5
```
If build fails: fix if trivial, log as "crash" if fundamental.

### Step 5: Benchmark
```bash
cd /home/gleb/sboxU && sage -python benchmark.py --verify
```

### Step 6: Decide Keep or Discard

**KEEP** if `correctness: PASS` AND any of:
- total_time_ms improved, OR
- ANY individual benchmark improved >5% vs best-ever, with no other regressing >5%, OR
- Code is SIMPLER (fewer lines, less complexity) with equal results

**DISCARD** if:
- `correctness: FAIL`
- No benchmark improved beyond measurement noise
- Build crashed and can't be fixed
- Small improvement but significant added complexity

If DISCARD: `git checkout -- sboxU/`

### Step 7: Log Results
Append to `results.tsv` (TAB-separated):
```
{commit_hash}	{total_time_ms}	{aes_self_ms}	{random_self_ms}	{random_nonequiv_ms}	{correctness}	{status}	{description}
```

### Step 8: Update Strategy
- Move tried idea to "Ideas Already Tried" with result and WHY it worked/failed
- Update "Current State" with new best if improved
- Add to "Exhausted Approaches" if a category of attempts is depleted
- Add new ideas if you discovered insights during implementation

### Step 9: Commit (if keeping)
```bash
cd /home/gleb/sboxU
git add -A && git commit -m "perf: {description}"
```

## Rules
1. ONE experiment per invocation
2. NEVER modify benchmark.py or baseline_checksums.json
3. Correctness is non-negotiable
4. Log EVERYTHING (even failures — they prevent re-trying bad ideas)
5. Update STRATEGY.md — it's your brain between sessions
6. Simple first — try simplest optimization before complex ones
7. Simplicity criterion: added complexity needs proportional improvement
8. Don't obsess over crashes — fix if trivial, skip if fundamental

## Key Optimization Targets

### Python layer (sboxU/ccz/affine_equivalence/cython_functions.pyx)
- `affine_equivalence_permutations()` — loops over 256 translations computing le_class_representative
- Uses Python dict for hash table — could use C++ std::unordered_map
- Redundant `table.keys()` call

### C++ core (sboxU/cpp/ccz/linear_representative.cpp)
- `compute_linear_representative<>()` — backtracking search with bit sets
- `subroutine()` — recursive search with pruning
- `update_linear()` — propagates linear constraints
- Set operations (`shift`, `intersect`, `unite`, `setminus`) — templated for SIMD

### C++ linear equivalence (sboxU/cpp/ccz/linear_equivalence.cpp)
- LEguess class for bijective guess-and-propagate
