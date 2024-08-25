import os
import binascii
import hashlib
import numpy as np
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from multiprocessing import Manager
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        addresses = {line.strip().lower() for line in file}
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

def generate_private_keys_rocm(batch_size):
    # Placeholder function for ROCm-based private key generation
    # Implement ROCm-specific code here
    return np.array([binascii.hexlify(os.urandom(32)).decode('utf-8') for _ in range(batch_size)])

async def generate_and_check(target_addresses, stop_event, counter, max_checks):
    batch_size = 1000  # Number of keys to generate per batch
    print_interval = 1000  # Print progress every 1000 addresses
    while not stop_event.is_set():
        # Generate a batch of private keys using ROCm
        private_keys_batch = generate_private_keys_rocm(batch_size)
        result = await asyncio.get_event_loop().run_in_executor(None, check_addresses, private_keys_batch, target_addresses)
        
        counter.value += batch_size
        if counter.value % print_interval == 0:
            # Print progress every 1000 addresses
            percentage_done = (counter.value / max_checks) * 100
            print(f"\rChecked {counter.value:,} addresses... {percentage_done:.2f}% done", end='')
        
        if result:
            stop_event.set()  # Signal other tasks to stop
            logging.info("Stopping all tasks due to match found.")
            return result
        
        if counter.value >= max_checks:
            stop_event.set()  # Stop if we reach the max number of checks
            logging.info(f"Reached maximum number of checks: {max_checks}. Stopping all tasks.")
            return None

async def main():
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    
    max_checks = int(input("Enter the number of addresses to check: "))

    manager = Manager()
    stop_event = asyncio.Event()
    counter = manager.Value('i', 0)  # Shared counter for address checks

    start_time = time.time()

    tasks = []
    num_workers = os.cpu_count() * 4  # Adjust based on your hardware capabilities

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        for _ in range(num_workers):
            tasks.append(loop.create_task(generate_and_check(target_addresses, stop_event, counter, max_checks)))
        
        await asyncio.gather(*tasks)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"All tasks have been stopped. Exiting script.")
    logging.info(f"Execution time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting...")
