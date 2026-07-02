#!/usr/bin/env python
import time
import benchmark

data = benchmark.prepare_data()
ae, get_sbox = data['imports']
aes_raw = data['aes']

# Create a different permutation from the first one
random_perm_a = data['random_perm_a']
aes = get_sbox(aes_raw)
other = get_sbox(random_perm_a)

# Warmup
for i in range(10):
    r = ae(aes, other)

n = 1000
t0 = time.perf_counter()
for i in range(n):
    r = ae(aes, other)
t1 = time.perf_counter()
print(f"ae(aes, other) non-self: {((t1-t0)/n)*1e6:.2f} us per call")