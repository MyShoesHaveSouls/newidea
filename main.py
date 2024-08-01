import hashlib
import binascii
import multiprocessing
import time
import os
from Crypto.Hash import keccak
from typing import List

# Function to convert a private key to an Ethereum address
def private_key_to_address(private_key: str) -> str:
    try:
        # Ensure the private key is valid hexadecimal and of correct length
        private_key_bytes = binascii.unhexlify(private_key)
        if len(private_key_bytes) != 32:
            raise ValueError("Invalid private key length")

        # Generate the Ethereum address
        k = keccak.new(digest_bits=256)
        k.update(private_key_bytes)
        address = k.hexdigest()[24:]  # Use only the last 20 bytes (40 hex chars)
        return address
    except (binascii.Error, ValueError) as e:
        print(f"Error with private key {private_key}: {e}")
        return None

# Function to check the balance of an Ethereum address
def check_address(private_key: str, addresses: List[str]) -> None:
    address = private_key_to_address(private_key)
    if address and address in addresses:
        print(f"Match found! Address: {address}, Private Key: {private_key}")

# Function to read private keys from a file
def load_private_keys(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        keys = [line.strip() for line in file if line.strip()]
    return keys

# Function to read addresses from a file
def load_addresses(file_path: str) -> List[str]:
    with open(file_path, 'r') as file:
        addresses = [line.strip() for line in file if line.strip()]
    return addresses

# Main function to start the process
def main():
    start_time = time.time()
    print("Starting script...")

    # Paths to files
    private_keys_file = 'private_keys.txt'  # Update with your actual file path
    addresses_file = 'addresses.txt'        # Update with your actual file path

    # Load private keys and addresses
    private_keys = load_private_keys(private_keys_file)
    addresses = load_addresses(addresses_file)

    if not private_keys:
        print("No private keys loaded. Please check your private_keys.txt file.")
        return
    if not addresses:
        print("No addresses loaded. Please check your addresses.txt file.")
        return

    print(f"Loaded {len(private_keys)} private keys.")
    print(f"Loaded {len(addresses)} addresses.")
    print("Starting address generation and checking...")

    # Use multiprocessing to speed up the checking process
    with multiprocessing.Pool() as pool:
        pool.starmap(check_address, [(key, addresses) for key in private_keys])

    execution_time = time.time() - start_time
    print(f"Execution time: {execution_time:.2f} seconds")

if __name__ == '__main__':
    main()
