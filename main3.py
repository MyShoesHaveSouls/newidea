import os
import binascii
from Crypto.Hash import keccak
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
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(private_key_bytes)
    return '0x' + keccak_hash.hexdigest()[-40:]

def check_address(private_key, target_addresses):
    address = private_key_to_address(private_key)
    if address.lower() in target_addresses:
        logging.info(f"Match found! Address: {address}, Private Key: {private_key}")
        return private_key, address
    return None

async def generate_and_check(target_addresses, stop_event, counter):
    loop = asyncio.get_event_loop()
    while not stop_event.is_set():
        private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
        result = await loop.run_in_executor(None, check_address, private_key, target_addresses)
        if result:
            stop_event.set()  # Signal other tasks to stop
            logging.info("Stopping all tasks due to match found.")
            return result
        else:
            counter.value += 1
            # Print the counter value periodically
            if counter.value % 1000 == 0:
                print(f"Checked {counter.value:,} addresses...")

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