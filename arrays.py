import os
import binascii
import hashlib
import numpy as np
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from multiprocessing import Manager

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

async def generate_and_check(target_addresses, stop_event, counter):
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
        print(f"\rChecked {counter.value:,} addresses...", end='')

async def main():
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)

    manager = Manager()
    stop_event = asyncio.Event()
    counter = manager.Value('i', 0)  # Shared counter for address checks

    tasks = []
    num_workers = os.cpu_count() * 2  # Adjust based on your hardware capabilities

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        loop = asyncio.get_event_loop()
        for _ in range(num_workers):
            tasks.append(loop.create_task(generate_and_check(target_addresses, stop_event, counter)))
        
        await asyncio.gather(*tasks)

    logging.info("All tasks have been stopped. Exiting script.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Script interrupted by user. Exiting...")
