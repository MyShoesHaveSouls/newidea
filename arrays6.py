import os
import binascii
import torch
import hashlib
import numpy as np
import asyncio
import logging
import time
from concurrent.futures import ProcessPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if ROCm is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.info(f"Using device: {device}")

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        addresses = {line.strip().lower() for line in file}
        logging.info(f"Loaded {len(addresses)} addresses.")
        return addresses

def private_key_to_address(private_key):
    # Convert to tensor
    private_key_bytes = torch.tensor(list(binascii.unhexlify(private_key)), dtype=torch.uint8, device=device)
    # Create Blake2b hash
    blake2b_hash = hashlib.blake2b(digest_size=32)
    blake2b_hash.update(private_key_bytes.cpu().numpy())
    return '0x' + blake2b_hash.hexdigest()[-40:]

def check_addresses(private_keys, target_addresses):
    for private_key in private_keys:
        address = private_key_to_address(private_key)
        if address.lower() in target_addresses:
            logging.info(f"Match found! Address: {address}, Private Key: {private_key}")
            return private_key, address
    return None

async def generate_and_check(target_addresses, stop_event, counter, max_checks):
    batch_size = 1000  # Number of keys to generate per batch
    while not stop_event.is_set():
        # Generate a batch of private keys
        private_keys_batch = np.array([binascii.hexlify(os.urandom(32)).decode('utf-8') for _ in range(batch_size)])
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

async def main():
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    
    max_checks = int(input("Enter the number of addresses to check: "))

    stop_event = asyncio.Event()
    counter = torch.multiprocessing.Value('i', 0)  # Shared counter for address checks

    start_time = time.time()

    # Automatically adjust the number of workers based on the GPU's capabilities
    num_workers = min(os.cpu_count() * 4, torch.cuda.get_device_properties(0).multi_processor_count * 2)
    logging.info(f"Using {num_workers} workers based on GPU capabilities.")

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.create_task(generate_and_check(target_addresses, stop_event, counter, max_checks))
            for _ in range(num_workers)
        ]
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
