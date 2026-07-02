#!/bin/bash
# AGR Loop — Ralph pattern for affine equivalence speed optimization
# Usage: bash run_agr.sh --max 10

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

MAX_ITERATIONS=100

while [[ $# -gt 0 ]]; do
    case $1 in
        --max) MAX_ITERATIONS=$2; shift 2 ;;
        *) shift ;;
    esac
done

echo "========================================"
echo " AGR: sboxU — Affine Equivalence Speed"
echo " Max iterations: $MAX_ITERATIONS"
echo "========================================"

for ((i=1; i<=MAX_ITERATIONS; i++)); do
    echo ""
    echo "=== ITERATION $i / $MAX_ITERATIONS [$(date '+%Y-%m-%d %H:%M:%S')] ==="
    echo ""

    claude -p "$(cat program.md)" \
        --dangerously-skip-permissions \
        --max-turns 100 \
        --effort high \
        2>&1 || true

    echo "--- Iteration $i done ---"
    sage -python analysis.py 2>/dev/null || true
    echo ""; cat results.tsv 2>/dev/null; echo ""
    sleep 2
done

echo "=== COMPLETE: $MAX_ITERATIONS iterations ==="
