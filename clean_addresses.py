import re

def clean_addresses_file(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        for line in lines:
            # Match Ethereum addresses in the line
            addresses = re.findall(r'0x[a-fA-F0-9]{40}', line)
            for address in addresses:
                outfile.write(f"{address}\n")
                
# Usage
input_file = 'addresses.txt'
output_file = 'cleaned_addresses.txt'
clean_addresses_file(input_file, output_file)
print(f"Cleaned addresses saved to {output_file}.")
