#!/usr/bin/env python3
import re
with open('benchmark_output.txt') as f:
    txt = f.read()
m = re.search(r'total_time_ms:\s+([\d.]+)', txt)
if m:
    total = float(m.group(1))
    print(f"total_time_ms: {total}")
m = re.search(r'aes_self_ms\s+([\d.]+)', txt)
if m:
    print(f"aes_self_ms: {m.group(1)}")
m = re.search(r'random_self_ms\s+([\d.]+)', txt)
if m:
    print(f"random_self_ms: {m.group(1)}")
m = re.search(r'random_nonequiv_ms\s+([\d.]+)', txt)
if m:
    print(f"random_nonequiv_ms: {m.group(1)}")