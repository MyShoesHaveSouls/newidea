import os
import secrets
import hashlib
import ecdsa
import multiprocessing
import datetime as dt

# Number of threads to use
threads = multiprocessing.cpu_count()
addressFile = 'addresses.txt'
foundFile = 'found.txt'

# Function to generate a random Ethereum private key
def generate_private_key():
    return secrets.token_bytes(32)

# Function to generate Ethereum address from private key
def private_key_to_address(private_key):
    # Convert private key to public key
    key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    public_key = key.get_verifying_key().to_string('compressed')
    
    # Generate address
    keccak = hashlib.new('keccak_256')
    keccak.update(public_key[1:])  # Skip the first byte (0x04)
    address = keccak.digest()[-20:]
    return '0x' + address.hex()

# Function to read Ethereum addresses from file
def read_addresses(filename):
    with open(filename, 'r') as f:
        addresses = [line.strip() for line in f]
    return set(addresses)

# Function to generate random Ethereum addresses and check them against a list
def generate_and_check_addresses(rawAddressSet, output_file):
    for _ in range(threads * 10**6):  # Limit the number of attempts for demonstration purposes
        private_key = generate_private_key()
        address = private_key_to_address(private_key)
        if address in rawAddressSet:
            message = f'Match found! Address: {address} has a private key: {private_key.hex()}'
            print(message)
            with open(output_file, 'a') as f:
                f.write(message + '\n')
            return  # Exit the function once a match is found

def run():
    rawAddressSet = read_addresses(addressFile)
    
    # Start processes
    processes = []
    for _ in range(threads):
        process = multiprocessing.Process(target=generate_and_check_addresses, args=(rawAddressSet, foundFile))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()

if __name__ == "__main__":
    try:
        start_time = dt.datetime.today().timestamp()
        run()
        end_time = dt.datetime.today().timestamp()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
    except Exception as e:
        print(f"Error: {e}")
