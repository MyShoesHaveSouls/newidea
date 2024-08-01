from multiprocessing import Pool
import hashlib
import binascii
import time

def private_key_to_address(private_key):
    """
    Convert a hexadecimal private key to an Ethereum address using keccak_256.
    """
    k = hashlib.new('sha3_256')
    k.update(binascii.unhexlify(private_key))
    address = k.hexdigest()[-40:]  # Last 40 hex characters
    return address

def check_address(private_key, addresses):
    """
    Check if the generated address from the private key is in the list of addresses.
    """
    address = private_key_to_address(private_key)
    if address in addresses:
        print(f"Match found! Address: {address}, Private Key: {private_key}")

def generate_and_check_addresses(private_keys, addresses):
    """
    Generate addresses from private keys and check against a list of addresses in parallel.
    """
    with Pool(processes=2) as pool:
        pool.starmap(check_address, [(key, addresses) for key in private_keys])

def load_addresses_from_file(filepath):
    """
    Load addresses from a file into a set.
    """
    with open(filepath, 'r') as file:
        addresses = {line.strip() for line in file}
    return addresses

def main():
    # Path to your addresses file
    addresses_file_path = './addresses.txt'
    
    print("Starting script...")
    
    # Load addresses
    addresses = load_addresses_from_file(addresses_file_path)
    print(f"Loaded {len(addresses)} addresses.")
    
    # Example private keys to test (Replace this with actual private keys you need to test)
    private_keys = [
        "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678",
        "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    ]
    
    print("Starting address generation and checking...")
    start_time = time.time()
    
    generate_and_check_addresses(private_keys, addresses)
    
    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
