import os
import secrets
import hashlib
import multiprocessing
import datetime as dt
from Crypto.Hash import SHA3_256

# Function to generate a new Ethereum address from a private key
def private_key_to_address(private_key):
    # Convert private key to address
    keccak = SHA3_256.new()
    keccak.update(private_key)
    address = keccak.digest()[-20:]
    return '0x' + address.hex()

# Function to check if the generated address matches any in the list
def check_address_in_list(address, address_set, private_key):
    if address in address_set:
        print(f"Match found! Address: {address}, Private Key: {private_key.hex()}")
        with open('found.txt', 'a') as f:
            f.write(f"Match found! Address: {address}, Private Key: {private_key.hex()}\n")
        return True
    return False

# Function to generate private keys and corresponding addresses
def generate_and_check_addresses(address_set):
    while True:
        # Generate a random private key
        private_key = secrets.token_bytes(32)
        # Generate address from the private key
        address = private_key_to_address(private_key)
        # Check if the address is in the address set
        if check_address_in_list(address, address_set, private_key):
            break

# Function to read Ethereum addresses from file
def read_addresses(filename):
    with open(filename, 'r') as f:
        addresses = [line.strip() for line in f]
    return set(addresses)

# Main function to start the address generation and checking process
def main():
    print("Starting script...")
    addresses = read_addresses('addresses.txt')
    print(f"Loaded {len(addresses)} addresses.")
    print("Starting address generation and checking...")
    generate_and_check_addresses(addresses)

if __name__ == "__main__":
    main()
