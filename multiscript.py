import os
import binascii
import hashlib
import numpy as np
import asyncio
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
from multiprocessing import Manager
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        data = file.read()

    addresses = {match.group(0).lower() for match in re.finditer(r'0x[a-fA-F0-9]{40}', data)}
    
    logging.info(f"Loaded {len(addresses)} addresses.")
    return addresses

def private_key_to_address(private_key):
    private_key_bytes = binascii.unhexlify(private_key)
    blake2b_hash = hashlib.blake2b(digest_size=32)
    blake2b_hash.update(private_key_bytes)
    return '0x' + blake2b_hash.hexdigest()[-40:]

def check_addresses(private_keys, target_addresses):
    for private_key in private_keys:
        address = private_key_to_address(private_key)
        if address.lower() in target_addresses:
            logging.info(f"Match found! Address: {address}, Private Key: {private_key}")
            return private_key, address
    return None

def worker(private_keys, target_addresses, stop_event, counter, max_checks):
    batch_size = 1000
    while not stop_event.is_set():
        private_keys_batch = np.array([binascii.hexlify(os.urandom(32)).decode('utf-8') for _ in range(batch_size)])
        result = check_addresses(private_keys_batch, target_addresses)
        if result:
            stop_event.set()
            logging.info("Stopping all tasks due to match found.")
            return result
        counter.value += batch_size
        if counter.value >= max_checks:
            stop_event.set()
            logging.info(f"Reached maximum number of checks: {max_checks}. Stopping all tasks.")
            return None
        print(f"\rChecked {counter.value:,} addresses...", end='')

async def run_parallel(target_addresses, max_checks, num_workers):
    manager = Manager()
    stop_event = manager.Event()
    counter = manager.Value('i', 0)

    start_time = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker, None, target_addresses, stop_event, counter, max_checks) for _ in range(num_workers)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                break

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"All tasks have been stopped. Exiting script.")
    logging.info(f"Execution time: {elapsed_time:.2f} seconds")

async def main():
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    
    max_checks = int(input("Enter the number of addresses to check: "))

    num_workers = os.cpu_count() * 4

    await run_parallel(target_addresses, max_checks, num_workers)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting...")
