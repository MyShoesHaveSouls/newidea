import os
import secrets
import hashlib
import ecdsa
import multiprocessing
import datetime as dt
from Crypto.Hash import keccak
from typing import Set

# Path to addresses.txt file and found.txt file
address_file = 'addresses.txt'
found_file = 'found.txt'

# Print start message
print("Starting script...")

# Function to read Ethereum addresses from file
def read_addresses(filename: str) -> Set[str]:
    with open(filename, 'r') as f:
        addresses = [line.strip() for line in f]
    return set(addresses)

# Function to convert private key to Ethereum address
def private_key_to_address(private_key: bytes) -> str:
    # Create a Keccak-256 hash of the private key
    k = keccak.Keccak256.new()
    k.update(private_key)
    # Ethereum address is the last 20 bytes of the hash
    return '0x' + k.digest()[-20:].hex()

# Function to generate random private keys and check them
def generate_and_check_addresses(address_set: Set[str]) -> None:
    while True:
        # Generate a random private key
        private_key = secrets.token_bytes(32)
        address = private_key_to_address(private_key)
        
        if address in address_set:
            print(f"Match found! Address: {address}, Private Key: {private_key.hex()}")
            with open(found_file, 'a') as f:
                f.write(f"Address: {address}, Private Key: {private_key.hex()}\n")
            break  # Stop after finding a match

# Main function to start the process
def main():
    addresses = read_addresses(address_file)
    print(f"Loaded {len(addresses)} addresses.")
    print("Starting address generation and checking...")
    generate_and_check_addresses(addresses)
    print("Script finished.")

if __name__ == "__main__":
    main()
