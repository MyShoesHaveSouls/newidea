import os
import binascii
from Crypto.Hash import keccak
import multiprocessing
import time
import sys

def load_addresses(file_path):
    """Load addresses from a file into a set."""
    with open(file_path, 'r') as file:
        return {line.strip().lower() for line in file}

def private_key_to_address(private_key):
    """Convert a private key to an Ethereum address."""
    private_key_bytes = binascii.unhexlify(private_key)
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(private_key_bytes)
    return '0x' + keccak_hash.hexdigest()[-40:]

def check_address(private_key, target_addresses, counter, lock, stop_event):
    """Check if the generated address matches any target address."""
    try:
        address = private_key_to_address(private_key)
        with lock:
            counter['value'] += 1
            sys.stdout.write(f"\rChecked: {counter['value']:,} addresses. Current Address: {address} from Private Key: {private_key}")
            sys.stdout.flush()
        if address.lower() in target_addresses:
            print(f"\nMatch found! Address: {address}, Private Key: {private_key}")
            stop_event.set()  # Signal other processes to stop
    except (ValueError, binascii.Error) as e:
        print(f"\nError with private key {private_key}: {str(e)}")

def generate_and_check_addresses(target_addresses, counter, lock, stop_event):
    """Generate random private keys and check them."""
    while not stop_event.is_set():
        private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_address(private_key, target_addresses, counter, lock, stop_event)

def main():
    """Main function to start the address generation and checking."""
    print("Starting script...")
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    print(f"Loaded {len(target_addresses)} addresses.")
    print("Starting address generation and checking...")

    # Initialize manager for shared state
    manager = multiprocessing.Manager()
    counter = manager.dict()
    counter['value'] = 0
    lock = manager.Lock()
    stop_event = manager.Event()

    start_time = time.time()

    # Number of workers should be equal to the number of CPU cores
    num_workers = 4  # Adjust this based on your VM’s capabilities

    try:
        with multiprocessing.Pool(processes=num_workers) as pool:
            # Use starmap to pass the stop_event
            pool.starmap(generate_and_check_addresses, [(target_addresses, counter, lock, stop_event)] * num_workers)
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
    finally:
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
