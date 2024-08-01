import os
import binascii
from Crypto.Hash import keccak
import multiprocessing
import time

def load_addresses(file_path):
    with open(file_path, 'r') as file:
        return {line.strip().lower() for line in file}

def private_key_to_address(private_key):
    private_key_bytes = binascii.unhexlify(private_key)
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(private_key_bytes)
    return '0x' + keccak_hash.hexdigest()[-40:]

def check_address(private_key, target_addresses):
    try:
        address = private_key_to_address(private_key)
        if address.lower() in target_addresses:
            print(f"Match found! Address: {address}, Private Key: {private_key}")
            os._exit(0)  # Stop the script
    except (ValueError, binascii.Error) as e:
        print(f"Error with private key {private_key}: {str(e)}")

def generate_and_check_addresses(target_addresses):
    while True:
        private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
        check_address(private_key, target_addresses)

def main():
    print("Starting script...")
    addresses_file = 'addresses.txt'
    target_addresses = load_addresses(addresses_file)
    print(f"Loaded {len(target_addresses)} addresses.")
    print("Starting address generation and checking...")

    start_time = time.time()
    try:
        with multiprocessing.Pool() as pool:
            pool.starmap(generate_and_check_addresses, [(target_addresses,)])
    except KeyboardInterrupt:
        print("Process interrupted.")
    except SystemExit:
        pass
    finally:
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
