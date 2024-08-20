from mnemonic import Mnemonic
import hashlib
import numpy as np
import itertools
import time
import sys
from multiprocessing import Pool, Manager

def generate_mnemonics_batch(word_list, batch_size):
    mnemo = Mnemonic("english")
    batch = []
    for phrase in itertools.product(word_list, repeat=12):
        batch.append(' '.join(phrase))
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def mnemonic_to_address(mnemonic):
    # Placeholder function. Implement actual conversion using libraries like bip32utils.
    return hashlib.sha256(mnemonic.encode()).hexdigest()[:40]

def check_addresses_batch(mnemonics, target_addresses, results):
    for mnemonic in mnemonics:
        address = mnemonic_to_address(mnemonic)
        if address in target_addresses:
            results.append((mnemonic, address))
            return

def check_addresses(target_addresses, word_list, num_phrases, batch_size):
    start_time = time.time()
    total_phrases = num_phrases
    checked_phrases = 0
    results = Manager().list()  # Shared list for results

    # Generate and process batches
    with Pool() as pool:
        for mnemonics_batch in generate_mnemonics_batch(word_list, batch_size):
            if checked_phrases >= num_phrases:
                break

            # Process batch in parallel
            pool.apply_async(
                check_addresses_batch,
                args=(mnemonics_batch, target_addresses, results),
                callback=lambda _: None  # No-op callback to prevent output
            )

            checked_phrases += len(mnemonics_batch)
            if checked_phrases % 100 == 0:  # Print ticker every 100 phrases
                percentage = (checked_phrases / total_phrases) * 100
                sys.stdout.write(f"\rChecked {checked_phrases:,} phrases ({percentage:.2f}%)...")
                sys.stdout.flush()

    # Ensure final output is printed
    sys.stdout.write(f"\rChecked {checked_phrases:,} phrases ({percentage:.2f}%)... Done!\n")
    sys.stdout.flush()

    # Check if any results were found
    if results:
        for mnemonic, address in results:
            print(f"Match found! Mnemonic: {mnemonic}, Address: {address}")

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")

def main():
    word_list_file = 'wordlist.txt'  # Path to your word list file
    target_addresses_file = 'target_addresses.txt'  # Path to your target addresses file

    # Load word list
    with open(word_list_file, 'r') as file:
        word_list = [line.strip() for line in file]

    # Load target addresses
    with open(target_addresses_file, 'r') as file:
        target_addresses = {line.strip().lower() for line in file}

    num_phrases = int(input("Enter the number of mnemonic phrases to try: "))
    batch_size = 1000  # Size of batches for processing

    check_addresses(target_addresses, word_list, num_phrases, batch_size)

if __name__ == "__main__":
    main()
