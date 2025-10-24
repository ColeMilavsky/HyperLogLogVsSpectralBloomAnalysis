# Referenced https://www.geeksforgeeks.org/system-design/hyperloglog-algorithm-in-system-design/ for implementation details

import math
import hashlib

# Number of registers (must be a power of 2)
m = 32
# Initialize registers
registers = [0] * m

def hash_function(value):
    hash_value = hashlib.sha256(value.encode('utf8')).hexdigest()
    return int(hash_value, 16)

def leftmost_1_bit_position(hash_value, p):
    bin_hash = bin(hash_value)[2:]
    return bin_hash.find('1', p) + 1

def process_element(element, registers, m):
    hash_value = hash_function(element)
    p = int(math.log2(m))
    register_index = hash_value & (m - 1)
    remaining_hash = hash_value >> p
    position = leftmost_1_bit_position(remaining_hash, p)
    registers[register_index] = max(registers[register_index], position)

def harmonic_mean(registers):
    sum_of_inverses = sum([2**-reg for reg in registers])
    return len(registers) / sum_of_inverses

def bias_correction(raw_estimate, m):
    if raw_estimate <= 2.5 * m:
        V = registers.count(0)
        if V > 0:
            return m * math.log(m / V)
    elif raw_estimate > (2**32) / 30:
        return -(2**32) * math.log(1 - raw_estimate / (2**32))
    return raw_estimate

def estimate_cardinality(registers):
    alpha_m = 0.7213 / (1 + 1.079 / len(registers))
    raw_estimate = alpha_m * len(registers)**2 * harmonic_mean(registers)
    return bias_correction(raw_estimate, len(registers))

def hyperloglog_estimate(dataset, m):
    registers = [0] * m
    for element in dataset:
        process_element(element, registers, m)
    return estimate_cardinality(registers)

# Example usage
for i in range(1000):
    process_element(f"element_{i}", registers, m)
dataset = [f"element_{i}" for i in range(1000)]
estimate = hyperloglog_estimate(dataset, m)
print(f"Estimated number of unique elements: {estimate}")
print(f"Actual number of unique elements: {len(set(dataset))}")