import os
import binascii
import hashlib
import numpy as np
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from multiprocessing import Manager, cpu_count
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        data = file.read()

    # Use a regular expression to extract all Ethereum addresses from the table
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

async def generate_and_check(target_addresses, stop_event, counter, max_checks, batch_size=1000):
    # Asynchronously generate private keys and check addresses
    while not stop_event.is_set():
        # Generate a batch of private keys
        private_keys_batch = np.array([binascii.hexlify(os.urandom(32)).decode('utf-8') for _ in range(batch_size)])
        # Run check_addresses in a separate thread to avoid blocking
        result = await asyncio.get_event_loop().run_in_executor(None, check_addresses, private_keys_batch, target_addresses)
        if result:
            stop_event.set()  # Signal other tasks to stop
            logging.info("Stopping all tasks due to match found.")
            return result
        counter.value += batch_size
        if counter.value >= max_checks:
            stop_event.set()  # Stop if we reach the max number of checks
            logging.info(f"Reached maximum number of checks: {max_checks}. Stopping all tasks.")
            return None
        print(f"\rChecked {counter.value:,} addresses...", end='')

async def worker(target_addresses, stop_event, counter, max_checks, batch_size=1000):
    # Worker function to run generate_and_check in asyncio loop
    await generate_and_check(target_addresses, stop_event, counter, max_checks, batch_size)

def run_parallel(target_addresses, max_checks, num_workers):
    # Manager for shared memory (counter and stop event)
    manager = Manager()
    stop_event = manager.Event()
    counter = manager.Value('i', 0)  # Shared counter for address checks

    # Create a ProcessPoolExecutor to run workers in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Create asyncio event loop for each worker
        futures = [executor.submit(asyncio.run, worker(target_addresses, stop_event, counter, max_checks)) for _ in range(num_workers)]

        # Wait for all processes to complete
        for future in futures:
            future.result()

def main():
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    
    max_checks = int(input("Enter the number of addresses to check: "))
    num_workers = cpu_count()  # Set to the number of CPU cores for optimal parallelism

    start_time = time.time()
    run_parallel(target_addresses, max_checks, num_workers)
    end_time = time.time()

    elapsed_time = end_time - start_time
    logging.info(f"All tasks have been stopped. Exiting script.")
    logging.info(f"Execution time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting...")
