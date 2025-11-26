# Main script to run the HyperLogLog and Spectral Bloom Filter algorithms

from algorithms.hyperLogLog import hyperloglog_estimate
from algorithms.SpectralBloomFilter import spectral_bloom_filter_estimate
from analysis.dataAnalysis import analyze_results

def main():
    # Grab dataset from data/raw/dataset.txt
    with open("data/raw/dataset.txt", "r") as f:
        dataset = [line.strip() for line in f.readlines()]
    
    # HyperLogLog estimation
    hll_estimate = hyperloglog_estimate(dataset, m=32)
    print(f"HyperLogLog Estimate: {hll_estimate}")
    
    # Spectral Bloom Filter estimation
    sbf_estimate = spectral_bloom_filter_estimate(dataset, size=1024, num_hashes=3)
    print(f"Spectral Bloom Filter Estimate: {sbf_estimate}")
    
    # Analyze results
    analyze_results(hll_estimate, sbf_estimate, len(set(dataset)))