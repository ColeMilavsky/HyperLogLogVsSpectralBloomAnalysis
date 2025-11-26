# Referenced https://theory.stanford.edu/~matias/papers/sbf-sigmod-03.pdf for implementation details
# Referenced https://www.geeksforgeeks.org/python/bloom-filters-introduction-and-python-implementation/
# Referenced HW4 Bloom Filter implementation for structure
# Spectral Bloom Filter Implementation in Python
# This implementation estimates the frequency of elements in a dataset

import numpy as np
import mmh3
import os
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
        #self.t = np.zeros((k, m), dtype=bool)
        self.t = np.zeros(m, dtype=int)  # Using int array for counting

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

        Hint(s):
        1. You will want to use self.hashing(...).
        2. We initialized our bit array to be of type
        boolean, so 1 should be represented as True, and 0 as 
        False.
        """
        #for i in range(self.k):
        #    self.t[i, self.hashing(x, i)] = True
        for i in range(self.k):
            self.t[self.hashing(x, i)] += 1

    def check(self, x) -> int:
        """
        :param x: The element to check how often it appears in the spectral bloom filter.
        :return: Int; Lowest value in the counting array for the positions
                 indicated by the hash functions for x.

        """
        min_count = float('inf')
        for i in range(self.k):
            min_count = min(min_count, self.t[self.hashing(x, i)])
        return min_count

if __name__ == '__main__':
    # You can test out things here. Feel free to write anything below.

    # Create a new bloom filter structure.
    # An example spectral bloom filter has 10 hash functions and 10,000,000 bits (10 MB)
    #   These values work well for datasets with roughly 1,000,000 unique elements
    # To ensure accuracy with larger datasets increase the number of bits proportionally
    bf = SpectralBloomFilter(k=10, m=10000000)

    print("Adding elements to Spectral Bloom Filter from dataset.txt")

    # Path to Data Directory
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/HyperLogLogVsSpectralBloomAnalysis/data/raw")

    # Create our spectral bloom filter of IPs
    seen_ips = np.genfromtxt(os.path.join(data_directory, 'dataset.txt'), dtype='str')
    for ip in seen_ips:
        bf.insert(ip)
        assert bf.check(ip)

    print("Computing Estimated Average Frequency of IPs in dataset.txt")

    # Calculate actual frequency from the data
    ip_counts = Counter(seen_ips)
    actual_frequencies = list(ip_counts.values())
    actual_avg = np.mean(actual_frequencies)

    # Calculate estimated frequency from SBF
    freq = []
    unique_ips = list(ip_counts.keys())
    for ip in unique_ips:
        freq.append(bf.check(ip))
    freq_avg = np.average(freq)

    # Calculate error
    err = abs(freq_avg - actual_avg) / actual_avg * 100

    print("Estimated Average Frequency: {}".format(freq_avg))
    print("Real Average Frequency: {}".format(actual_avg))
    print("Error: {}%".format(err))