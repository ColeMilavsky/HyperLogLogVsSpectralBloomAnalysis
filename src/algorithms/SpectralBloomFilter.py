# Referenced https://theory.stanford.edu/~matias/papers/sbf-sigmod-03.pdf for implementation details
# Referenced https://www.geeksforgeeks.org/python/bloom-filters-introduction-and-python-implementation/
# Referenced HW4 Bloom Filter implementation for structure
# Spectral Bloom Filter Implementation in Python
# This implementation estimates the frequency of elements in a dataset

import numpy as np
import mmh3
import os
import pandas as pd
from collections import Counter

class SpectralBloomFilter:
    def __init__(self, k:int = 10, m:int=100000):
        """
        :param k: The number of hash functions (rows).
        :param m: The number of buckets (cols).

        Initializes the bloom filter to all zeros, as a
        boolean array where True = 1 and False = 0.
        
        """
        self.k = k
        self.m = m
        self.t = np.zeros(m, dtype=int)

    def hashing(self, x, i:int) -> int:
        """
        :param x: The element x to be hashed.
        :param i: Which hash function to use, for i=0,...,self.k-1.
        :return: h_i(x) the ith hash function applied to x. We take the hash value and mod
        it by our table size. This consistent hashing function doesn't rely on
        randomness, and will uniformly distribute a set of n inputs across m buckets
        (even with different values of m, the distribution of inputs will still be
        roughly uniform)
        """
        return mmh3.hash(str(x), i) % self.m

    def insert(self, x):
        """
        :param x: The element to add to the bloom filter.
        
        In this function, we add x to our bloom filter.
        """
        for i in range(self.k):
            self.t[self.hashing(x, i)] += 1

    def get_expected_error(self, data_size:int) -> float:
        """
        Calculate the expected overestimation error E_SBF from the paper.
        E_SBF = E_b ≈ (1 - e^(-kn/m))^k
        
        :param data_size: The total number of insertions (n)
        :return: Expected error E_b
        """
        if self.m == 0 or data_size == 0:
            return 0.0
        exponent = -self.k * data_size / self.m
        return (1 - np.exp(exponent)) ** self.k

    def check(self, x, apply_correction=False, data_size:int = None) -> float:
        """
        :param x: The element to check how often it appears in the spectral bloom filter.
        :param apply_correction: Bool; Whether to apply the bias correction.
        :param data_size: Int; The number of elements inserted into the SBF (required if apply_correction=True).
        :return: Float; Estimated frequency of x.
        """
        min_count = float('inf')
        for i in range(self.k):
            min_count = min(min_count, self.t[self.hashing(x, i)])
    
        if apply_correction:
            if data_size is None:
                raise ValueError("data_size must be provided when apply_correction=True")
            # Subtract expected error as per the paper - PER ELEMENT
            expected_error = self.get_expected_error(data_size)
            # The corrected estimate should never go below 0
            corrected_estimate = max(0.0, min_count - expected_error)
            return corrected_estimate
        else:
            return float(min_count)

if __name__ == '__main__':
    # Path to Data Directory
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/data/raw")
    processed_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/data/processed")

    # Create processed directory if it doesn't exist
    os.makedirs(processed_directory, exist_ok=True)

    # Array of bucket sizes (m values)
    bucket_sizes = [100000000, 200000000, 300000000, 400000000, 500000000]
    
    # Define datasets to test
    datasets = [
        ('dataset_100m.txt', 'spectral_bloom_filter_results_100m_E_b_fix.xlsx')
    ]
    
    # Test each dataset
    for dataset_file, output_filename in datasets:
        # Array to store results for this dataset
        sbf_arr = []

        print(f"\n{'='*60}")
        print(f"Processing {dataset_file}")
        print(f"{'='*60}\n")

        # Test different bucket sizes
        for m in bucket_sizes:
            # Create a new bloom filter structure
            bf = SpectralBloomFilter(k=10, m=m)

            print(f"Adding elements to Spectral Bloom Filter from {dataset_file} (m={m:,})")

            # STREAM the dataset instead of loading all at once
            dataset_path = os.path.join(data_directory, dataset_file)
            n = 0  # Count total insertions
            ip_counter = Counter()  # Track frequencies
            
            with open(dataset_path, 'r') as f:
                for line in f:
                    ip = line.strip()
                    if ip:  # Skip empty lines
                        bf.insert(ip)
                        ip_counter[ip] += 1
                        n += 1
                        
                        # Progress indicator
                        if n % 10000000 == 0:
                            print(f"  Processed {n:,} IPs...")

            print(f"  Total IPs processed: {n:,}")
            print(f"  Unique IPs: {len(ip_counter):,}")
            
            # Sanity check - verify at least one element exists
            first_ip = next(iter(ip_counter.keys()))
            assert bf.check(first_ip, apply_correction=False) > 0

            print(f"Computing Estimated Average Frequency of IPs (m={m:,})")
            
            # Calculate actual frequency from the counter
            actual_frequencies = list(ip_counter.values())
            actual_avg = np.mean(actual_frequencies)
            
            # Calculate expected error
            expected_error = bf.get_expected_error(n)
            
            # Calculate estimated frequency UNCORRECTED
            freq_uncorrected = []
            for ip in ip_counter.keys():
                freq_uncorrected.append(bf.check(ip, apply_correction=False))
            freq_avg_uncorrected = np.average(freq_uncorrected)

            # Calculate estimated frequency CORRECTED
            freq_corrected = []
            for ip in ip_counter.keys():
                corrected_freq = bf.check(ip, apply_correction=True, data_size=n)
                freq_corrected.append(corrected_freq)
            freq_avg_corrected = np.average(freq_corrected)
            
            # Store results
            sbf_arr.append((m, freq_avg_corrected, actual_avg, expected_error, freq_avg_uncorrected))
            
            print(f"Expected Error (E_b):      {expected_error:.6f}")
            print(f"Uncorrected Avg Frequency: {freq_avg_uncorrected:.4f}")
            print(f"Corrected Avg Frequency:   {freq_avg_corrected:.4f}")
            print(f"Real Average Frequency:    {actual_avg:.4f}")
            print(f"Error (corrected):         {abs(freq_avg_corrected - actual_avg) / actual_avg * 100:.2f}%")
            print(f"Error (uncorrected):       {abs(freq_avg_uncorrected - actual_avg) / actual_avg * 100:.2f}%\n")

        # Create results Excel file from sbf_arr
        results_data = {
            'Buckets (m)': [entry[0] for entry in sbf_arr],
            'Corrected Avg Frequency': [entry[1] for entry in sbf_arr],
            'Actual Avg Frequency': [entry[2] for entry in sbf_arr],
            'Expected Error (E_b)': [entry[3] for entry in sbf_arr],
            'Uncorrected Avg Frequency': [entry[4] for entry in sbf_arr],
            'Error Corrected (%)': [abs(entry[1] - entry[2]) / entry[2] * 100 for entry in sbf_arr],
            'Error Uncorrected (%)': [abs(entry[4] - entry[2]) / entry[2] * 100 for entry in sbf_arr]
        }
        out_excel = pd.DataFrame(results_data)
        
        # Save to Excel
        output_file = os.path.join(processed_directory, output_filename)
        out_excel.to_excel(output_file, index=False, sheet_name='SBF Results')
        
        print(f"Results saved to: {output_file}\n")