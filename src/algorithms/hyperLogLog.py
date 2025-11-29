# Referenced https://www.geeksforgeeks.org/system-design/hyperloglog-algorithm-in-system-design/ for implementation details
# HyperLogLog Algorithm Implementation in Python
# This implementation estimates the number of unique elements in a dataset

import math
import hashlib
import numpy as np
import os
import pandas as pd
from collections import Counter

class HyperLogLog:
    def __init__(self, m:int = 32):
        """
        param m: The number of registers (must be a power of 2).
        
        Initializes the HyperLogLog with m registers, all set to 0.
        """
        self.m = m
        self.p = int(math.log2(m))
        self.registers = [0] * m
        self.alpha_m = self._get_alpha_m()
    
    def _get_alpha_m(self):
        """
        Calculate the bias correction constant alpha_m.
        """
        if self.m >= 128:
            return 0.7213 / (1 + 1.079 / self.m)
        elif self.m >= 64:
            return 0.709
        elif self.m >= 32:
            return 0.697
        elif self.m >= 16:
            return 0.673
        else:
            return 0.5
    
    def hash_function(self, x):
        """
        param x: The element to hash.
        return: Integer hash value of the element.
        
        Hash function to convert element to integer hash value.
        """
        return int(hashlib.md5(str(x).encode()).hexdigest(), 16)
    
    def leftmost_1_bit_position(self, hash_value):
        """
        Find position of first 1-bit (rho function in HLL paper).
        Returns the number of leading zeros + 1.
        """
        if hash_value == 0:
            return (128 - self.p) + 1

        # Force to fixed 128 bits
        remainder_bits = 128 - self.p
        binary = bin(hash_value)[2:].zfill(remainder_bits)

        # Count leading zeros
        leading_zeros = binary.find('1')
        return leading_zeros + 1
    
    def insert(self, x):
        """
        param x: The element to add to the HyperLogLog.
        
        Process and add an element to the HyperLogLog structure.
        """
        hash_value = self.hash_function(x)
        register_index = hash_value & (self.m - 1)
        remaining_hash = hash_value >> self.p
        position = self.leftmost_1_bit_position(remaining_hash)
        self.registers[register_index] = max(self.registers[register_index], position)
    
    def harmonic_mean(self):
        """
        Calculate Z = 1 / sum(2^-M[j]) where M[j] are the registers.
        """
        sum_of_inverses = sum([2**-reg for reg in self.registers])
        
        # Prevent division by zero
        if sum_of_inverses == 0:
            return float('inf')
        
        # Z = 1 / sum(2^-M[j])
        return 1.0 / sum_of_inverses

    
    def estimate_cardinality(self, use_bias_correction=True):
        """
        return: Estimated number of unique elements.
        
        Estimate the cardinality using the HyperLogLog algorithm with optional bias correction.
        """
        harmonic = self.harmonic_mean()
        
        # Handle edge case
        if harmonic == float('inf'):
            return 0.0
        
        raw_estimate = float(self.alpha_m) * float(self.m ** 2) * float(harmonic)
        
        if not use_bias_correction:
            return raw_estimate
        
        # Bias Correction for small cardinalities
        if raw_estimate <= 2.5 * self.m:
            V = self.registers.count(0)
            if V > 0:
                return float(self.m) * math.log(float(self.m) / float(V))
        elif raw_estimate <= (2**32) / 30:
            return raw_estimate
        else:
            # Large range correction
            ratio = raw_estimate / (2**32)
            if ratio < 1:
                return -(2**32) * math.log(1 - ratio)
            else:
                return raw_estimate
        
        return raw_estimate

if __name__ == '__main__':
    # Path to Data Directory
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/data/raw")
    processed_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/data/processed")

    # Create processed directory if it doesn't exist
    os.makedirs(processed_directory, exist_ok=True)

    # Array of register sizes
    register_sizes = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    # Define datasets to test
    datasets = [
        ('dataset_1m.txt', 'hyperloglog_results_1m_bias_comparison.xlsx'),
        ('dataset_10m.txt', 'hyperloglog_results_10m_bias_comparison.xlsx'),
        ('dataset_100m.txt', 'hyperloglog_results_100m_bias_comparison.xlsx')
    ]

    # Test each dataset
    for dataset_file, output_filename in datasets:
        print(f"\n{'='*60}")
        print(f"Processing {dataset_file}")
        print(f"{'='*60}\n")

        # Load dataset ONCE
        print("Loading dataset...")
        dataset_path = os.path.join(data_directory, dataset_file)
        seen_ips_list = []
        with open(dataset_path, 'r') as f:
            for line in f:
                ip = line.strip()
                if ip:
                    seen_ips_list.append(ip)
        seen_ips = np.array(seen_ips_list)
        actual_unique = len(set(seen_ips))
        print(f"Loaded {len(seen_ips):,} IPs ({actual_unique:,} unique)\n")

        # Arrays for with and without bias correction
        hll_arr_with = []
        hll_arr_without = []

        # Create a new HyperLogLog structure of varying register sizes
        for size in register_sizes:
            m = 2**size
            hll_size = HyperLogLog(m=m)
        
            # Add IPs to HyperLogLog
            print(f"Processing m = {m:,} (2^{size})...")
            for ip in seen_ips:
                hll_size.insert(ip)
        
            # Estimate WITH bias correction
            estimate_with = hll_size.estimate_cardinality(use_bias_correction=True)
            error_with = abs(estimate_with - actual_unique) / actual_unique * 100
            hll_arr_with.append((m, estimate_with, actual_unique, error_with))
            
            # Estimate WITHOUT bias correction
            estimate_without = hll_size.estimate_cardinality(use_bias_correction=False)
            error_without = abs(estimate_without - actual_unique) / actual_unique * 100
            hll_arr_without.append((m, estimate_without, actual_unique, error_without))

            print(f"  WITH bias correction:    {estimate_with:>12,.0f} (error: {error_with:6.2f}%)")
            print(f"  WITHOUT bias correction: {estimate_without:>12,.0f} (error: {error_without:6.2f}%)")
            print(f"  Actual unique IPs:       {actual_unique:>12,}")
            print()

        # Create results Excel file - WITH bias correction
        results_with = pd.DataFrame({
            'Registers (m)': [entry[0] for entry in hll_arr_with],
            'Estimated Unique': [int(entry[1]) for entry in hll_arr_with],
            'Actual Unique': [entry[2] for entry in hll_arr_with],
            'Error (%)': [entry[3] for entry in hll_arr_with]
        })
        
        # Create results Excel file - WITHOUT bias correction
        results_without = pd.DataFrame({
            'Registers (m)': [entry[0] for entry in hll_arr_without],
            'Estimated Unique': [int(entry[1]) for entry in hll_arr_without],
            'Actual Unique': [entry[2] for entry in hll_arr_without],
            'Error (%)': [entry[3] for entry in hll_arr_without]
        })
        
        # Save both to Excel file with separate sheets
        output_file = os.path.join(processed_directory, output_filename)
        with pd.ExcelWriter(output_file) as writer:
            results_with.to_excel(writer, index=False, sheet_name='With Bias Correction')
            results_without.to_excel(writer, index=False, sheet_name='Without Bias Correction')
        
        print(f"Results saved to: {output_file}")
        print(f"\nSummary for {dataset_file}:")
        print(f"Best WITH bias:    {min(e[3] for e in hll_arr_with):.2f}% at m={[e[0] for e in hll_arr_with if e[3] == min(e[3] for e in hll_arr_with)][0]:,}")
        print(f"Best WITHOUT bias: {min(e[3] for e in hll_arr_without):.2f}% at m={[e[0] for e in hll_arr_without if e[3] == min(e[3] for e in hll_arr_without)][0]:,}")