import os
import binascii
from Crypto.Hash import keccak
import multiprocessing
import time
import sys
from multiprocessing import Value, Lock

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        return {line.strip().lower() for line in file}

def private_key_to_address(private_key):
    private_key_bytes = binascii.unhexlify(private_key)
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(private_key_bytes)
    return '0x' + keccak_hash.hexdigest()[-40:]

def check_address(private_key, target_addresses, counter, lock):
    try:
        address = private_key_to_address(private_key)
        with lock:
            counter.value += 1
            sys.stdout.write(f"\rChecked: {counter.value:,} addresses. Current Address: {address} from Private Key: {private_key}")
            sys.stdout.flush()
        if address.lower() in target_addresses:
            print(f"\nMatch found! Address: {address}, Private Key: {private_key}")
            os._exit(0)  # Stop the script
    except (ValueError, binascii.Error) as e:
        print(f"\nError with private key {private_key}: {str(e)}")

def generate_and_check_addresses(target_addresses, counter, lock):
    while True:
        private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_address(private_key, target_addresses, counter, lock)

def main():
    print("Starting script...")
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    print(f"Loaded {len(target_addresses)} addresses.")
    print("Starting address generation and checking...")

    # Initialize counter and lock for multiprocessing
    counter = Value('i', 0)
    lock = Lock()

    start_time = time.time()
    try:
        with multiprocessing.Pool() as pool:
            pool.starmap(generate_and_check_addresses, [(target_addresses, counter, lock)])
    except KeyboardInterrupt:
        print("\nProcess interrupted.")
    except SystemExit:
        pass
    finally:
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
