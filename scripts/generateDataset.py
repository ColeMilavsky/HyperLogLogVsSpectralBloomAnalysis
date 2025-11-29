# This script generates a synthetic dataset for testing the HyperLogLog and Spectral Bloom Filter algorithms

import random
import os

def generate_dataset(num_elements, unique_ratio=0.8):
    dataset = []
    
    # Generate IPs with different frequency patterns
    # 20% of elements are from frequent visitors (10-50 visits each)
    # 30% of elements are from occasional visitors (3-9 visits each)
    # 50% of elements are from rare visitors (1-2 visits each)

    # Total Unique IPs: ((20% / 30) + (30% / 6) + (50% / 1.5)) * num_elements = .39 * num_elements
    #   For 10000 elements, this gives 3900 unique IPs
    # Average Frequency Calculation: num_elements / (.39 * num_elements) = 1 / .39 = ~2.56

    # 20% frequent visitors (10-50 visits each)
    num_frequent = int(num_elements * 0.20)
    frequent_ips = [f"192.168.1.{i}" for i in range(num_frequent // 30)]
    for ip in frequent_ips:
        dataset.extend([ip] * random.randint(10, 50))
    
    # 30% occasional visitors (3-9 visits each)
    num_occasional = int(num_elements * 0.30)
    occasional_ips = [f"10.0.{i//256}.{i%256}" for i in range(num_occasional // 6)]
    for ip in occasional_ips:
        dataset.extend([ip] * random.randint(3, 9))
    
    # 50% rare visitors (1-2 visits each)
    num_rare = num_elements - len(dataset)
    rare_ips = [f"172.16.{i//256}.{i%256}" for i in range(num_rare)]
    for ip in rare_ips:
        dataset.extend([ip] * random.randint(1, 2))
    
    # Trim to exact size and shuffle
    dataset = dataset[:num_elements]
    random.shuffle(dataset)
    return dataset

def main():
    # Create three datasets of varying sizes
    num_elements_1m = 1000000
    num_elements_10m = 10000000
    num_elements_100m = 100000000

    dataset_1m = generate_dataset(num_elements_1m)
    dataset_10m = generate_dataset(num_elements_10m)
    dataset_100m = generate_dataset(num_elements_100m)

    # Path to Data Directory
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, "HyperLogLogVsSpectralBloomAnalysis/data/raw")
    
    # Save to file
    with open(os.path.join(data_directory, "dataset_1m.txt"), "w") as f:
        for element in dataset_1m:
            f.write(f"{element}\n")
    with open(os.path.join(data_directory, "dataset_10m.txt"), "w") as f:
        for element in dataset_10m:
            f.write(f"{element}\n")
    with open(os.path.join(data_directory, "dataset_100m.txt"), "w") as f:
        for element in dataset_100m:
            f.write(f"{element}\n")

if __name__ == "__main__":
    main()