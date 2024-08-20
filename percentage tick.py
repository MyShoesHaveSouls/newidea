import os
import binascii
from Crypto.Hash import keccak
import numpy as np
import logging
import time
from multiprocessing import Pool, Manager, Lock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_addresses(file_path):
    addresses = set()
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('0x') and len(line) == 42:  # Ethereum addresses are 42 chars including '0x'
                addresses.add(line.lower())
    logging.info(f"Loaded {len(addresses)} addresses.")
    return addresses

def private_key_to_address(private_key):
    private_key_bytes = binascii.unhexlify(private_key)
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(private_key_bytes)
    return '0x' + keccak_hash.hexdigest()[-40:]

def check_address(private_key, target_addresses, counter, lock, total_addresses):
    try:
        address = private_key_to_address(private_key)
        with lock:
            counter['value'] += 1
            if counter['value'] % 100 == 0:
                percent_complete = (counter['value'] / total_addresses) * 100
                logging.info(f"Checked {counter['value']:,} addresses ({percent_complete:.2f}% complete)...")
        if address in target_addresses:
            print(f"\nMatch found! Address: {address}, Private Key: {private_key}")
            os._exit(0)
    except (ValueError, binascii.Error) as e:
        logging.error(f"Error with private key {private_key}: {str(e)}")

def generate_and_check_addresses(target_addresses, counter, lock, num_addresses):
    for _ in range(num_addresses):
        private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_address(private_key, target_addresses, counter, lock, num_addresses)

def main():
    addresses_file = 'addresses.txt'
    num_addresses_to_check = int(input("Enter the number of addresses to check: "))
    
    target_addresses = load_addresses(addresses_file)
    
    if num_addresses_to_check > len(target_addresses):
        print(f"Warning: You are trying to check more addresses than available ({len(target_addresses)}). Adjusting to maximum available.")
        num_addresses_to_check = len(target_addresses)
    
    manager = Manager()
    counter = manager.dict()
    counter['value'] = 0
    lock = manager.Lock()
    
    start_time = time.time()
    with Pool() as pool:
        pool.starmap(generate_and_check_addresses, [(target_addresses, counter, lock, num_addresses_to_check)])
    
    end_time = time.time()
    logging.info(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
