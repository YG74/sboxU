#!/usr/bin/env python
import time
import benchmark

data = benchmark.prepare_data()
ae, get_sbox = data['imports']
aes_raw = data['aes']

# Warmup
for i in range(10):
    aes = get_sbox(aes_raw)
    r = ae(aes, aes)

n = 1000
t0 = time.perf_counter()
for i in range(n):
    aes = get_sbox(aes_raw)
    r = ae(aes, aes)
t1 = time.perf_counter()
print(f"Full per-call: {((t1-t0)/n)*1e6:.2f} us")