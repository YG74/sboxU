#!/usr/bin/env python
import time
import benchmark

# Prepare data once
data = benchmark.prepare_data()

# Warmup
for i in range(10):
    benchmark.bench_aes_self(data)
    benchmark.bench_random_self(data)
    benchmark.bench_random_nonequiv(data)

n = 1000
t0 = time.perf_counter()
for i in range(n):
    benchmark.bench_aes_self(data)
t1 = time.perf_counter()
print(f"aes_self: {((t1-t0)/n)*1e6:.2f} us per call")

t0 = time.perf_counter()
for i in range(n):
    benchmark.bench_random_self(data)
t1 = time.perf_counter()
print(f"random_self: {((t1-t0)/n)*1e6:.2f} us per call")

t0 = time.perf_counter()
for i in range(n):
    benchmark.bench_random_nonequiv(data)
t1 = time.perf_counter()
print(f"random_nonequiv: {((t1-t0)/n)*1e6:.2f} us per call")