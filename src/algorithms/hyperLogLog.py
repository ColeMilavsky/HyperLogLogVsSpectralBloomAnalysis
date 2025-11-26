# Referenced https://www.geeksforgeeks.org/system-design/hyperloglog-algorithm-in-system-design/ for implementation details
# HyperLogLog Algorithm Implementation in Python
# This implementation estimates the number of unique elements in a dataset

import math
import hashlib
import numpy as np
import os

class HyperLogLog:
    def __init__(self, m:int = 32):
        """
        :param m: The number of registers (must be a power of 2).
        
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
        return 0.7213 / (1 + 1.079 / self.m)
    
    def hash_function(self, x):
        """
        :param x: The element to hash.
        :return: Integer hash value of the element.
        
        Hash function to convert element to integer hash value.
        """
        return int(hashlib.md5(str(x).encode()).hexdigest(), 16)
    
    def leftmost_1_bit_position(self, hash_value):
        """
        :param hash_value: The hash value to process.
        :return: Position of the leftmost 1 bit.
        
        Find the position of the leftmost 1 bit in the binary representation.
        """
        bin_hash = bin(hash_value)[2:]
        position = bin_hash.find('1') + 1
        return position if position > 0 else len(bin_hash) + 1
    
    def insert(self, x):
        """
        :param x: The element to add to the HyperLogLog.
        
        Process and add an element to the HyperLogLog structure.
        """
        hash_value = self.hash_function(x)
        register_index = hash_value & (self.m - 1)
        remaining_hash = hash_value >> self.p
        position = self.leftmost_1_bit_position(remaining_hash)
        self.registers[register_index] = max(self.registers[register_index], position)
    
    def harmonic_mean(self):
        """
        Calculate the harmonic mean of the registers.
        """
        sum_of_inverses = sum([2**-reg for reg in self.registers])
        return self.m / sum_of_inverses
    
    def estimate_cardinality(self):
        """
        :return: Estimated number of unique elements.
        
        Estimate the cardinality using the HyperLogLog algorithm with bias correction.
        """
        raw_estimate = self.alpha_m * (self.m ** 2) * self.harmonic_mean()
        
        # Bias Correction
        if raw_estimate <= 2.5 * self.m:
            V = self.registers.count(0)
            if V > 0:
                return self.m * math.log(self.m / V)
        elif raw_estimate > (2**32) / 30:
            return -(2**32) * math.log(1 - raw_estimate / (2**32))
        
        return raw_estimate

if __name__ == '__main__':
    # You can test out things here. Feel free to write anything below.
    
    # Create a new HyperLogLog structure
    # An example HyperLogLog has 512 registers
    #   This value works well for datasets with roughly 390,000 unique elements
    # To ensure accuracy with larger datasets increase the number of registers proportionally
    hll = HyperLogLog(m=512)
    
    print("Adding elements to HyperLogLog from dataset.txt")
    
    # Path to Data Directory
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/HyperLogLogVsSpectralBloomAnalysis/data/raw")
    
    # Add IPs to HyperLogLog
    seen_ips = np.genfromtxt(os.path.join(data_directory, 'dataset.txt'), dtype='str')
    for ip in seen_ips:
        hll.insert(ip)
    
    print("Computing Estimated Number of Unique IPs in dataset.txt")
    estimate = hll.estimate_cardinality()
    actual_unique = len(set(seen_ips))
    print(f"Estimated number of unique IPs: {estimate:.0f}")
    print(f"Actual number of unique IPs: {actual_unique}")
    print(f"Error: {abs(estimate - actual_unique) / actual_unique * 100:.2f}%")