import time
import sqlite3
import requests

ETHERSCAN_API_KEY = ''
ETHERSCAN_API_URL = 'https://api.etherscan.io/api'
DATABASE_FILE = 'database.db'

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            address TEXT PRIMARY KEY,
            balance REAL,
            FOREIGN KEY(address) REFERENCES wallets(address)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS erc20_tokens (
            address TEXT,
            token_name TEXT,
            token_symbol TEXT,
            balance REAL,
            FOREIGN KEY(address) REFERENCES wallets(address),
            PRIMARY KEY(address, token_name)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS nfts (
            address TEXT,
            nft_id TEXT,
            nft_name TEXT,
            FOREIGN KEY(address) REFERENCES wallets(address),
            PRIMARY KEY(address, nft_id)
        )
    ''')

    conn.commit()
    conn.close()

def get_recent_transactions():
    params = {
        'module': 'proxy',
        'action': 'eth_getBlockByNumber',
        'tag': 'latest',
        'boolean': 'true',
        'apikey': ETHERSCAN_API_KEY
    }
    response = requests.get(ETHERSCAN_API_URL, params=params)
    data = response.json()

    if data['status'] == '1' and 'result' in data:
        return data['result']['transactions']
    else:
        print(f"Error fetching transactions: {data.get('result', 'Unknown error')}")
        return []

def get_wallet_from_transaction(transaction):
    from_wallet = transaction['from']
    to_wallet = transaction['to']
    return from_wallet, to_wallet

def get_balance(address):
    params = {
        'module': 'account',
        'action': 'balance',
        'address': address,
        'tag': 'latest',
        'apikey': ETHERSCAN_API_KEY
    }
    response = requests.get(ETHERSCAN_API_URL, params=params)
    data = response.json()

    if data['status'] == '1' and 'result' in data:
        balance = int(data['result']) / 1e18  # Convert from Wei to ETH
        return balance
    else:
        print(f"Error fetching balance for {address}: {data.get('result', 'Unknown error')}")
        return 0

def update_database_with_wallets(wallets):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    for address in wallets:
        c.execute('''
            INSERT OR IGNORE INTO wallets (address)
            VALUES (?)
        ''', (address,))
    
    conn.commit()
    conn.close()

def update_balance(address, balance):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    c.execute('''
        INSERT OR REPLACE INTO balances (address, balance)
        VALUES (?, ?)
    ''', (address, balance))
    
    conn.commit()
    conn.close()

def update_erc20_tokens(address, tokens):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    for token in tokens:
        c.execute('''
            INSERT OR REPLACE INTO erc20_tokens (address, token_name, token_symbol, balance)
            VALUES (?, ?, ?, ?)
        ''', (address, token['name'], token['symbol'], token['balance']))
    
    conn.commit()
    conn.close()

def update_nfts(address, nfts):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    for nft in nfts:
        c.execute('''
            INSERT OR REPLACE INTO nfts (address, nft_id, nft_name)
            VALUES (?, ?, ?)
        ''', (address, nft['id'], nft['name']))
    
    conn.commit()
    conn.close()

def fetch_erc20_tokens(address):
    tokens = [
        {'contract_address': '0x1234567890abcdef1234567890abcdef12345678', 'name': 'TokenA', 'symbol': 'TKA'},
        {'contract_address': '0xabcdef1234567890abcdef1234567890abcdef12', 'name': 'TokenB', 'symbol': 'TKB'},
    ]
    
    erc20_tokens = []
    for token in tokens:
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': token['contract_address'],
            'address': address,
            'tag': 'latest',
            'apikey': ETHERSCAN_API_KEY
        }
        response = requests.get(ETHERSCAN_API_URL, params=params)
        data = response.json()

        if data['status'] == '1' and 'result' in data:
            balance = int(data['result']) / 10**18  # Convert from Wei to Token units
            erc20_tokens.append({
                'name': token['name'],
                'symbol': token['symbol'],
                'balance': balance
            })
        else:
            print(f"Error fetching ERC-20 balance for {address}: {data.get('result', 'Unknown error')}")
    
    return erc20_tokens

def fetch_nfts(address):
    opensea_url = f'https://api.opensea.io/api/v1/assets?owner={address}&order_direction=desc&offset=0&limit=50'
    response = requests.get(opensea_url)
    data = response.json()

    nfts = []
    if 'assets' in data:
        for asset in data['assets']:
            nft_id = asset.get('token_id')
            nft_name = asset.get('name', 'Unknown NFT')
            nfts.append({
                'id': nft_id,
                'name': nft_name
            })
    else:
        print(f"Error fetching NFTs for {address}: {data.get('error', 'Unknown error')}")
    
    return nfts

def main():
    initialize_database()
    seen_wallets = set()

    while True:
        try:
            transactions = get_recent_transactions()
            new_wallets = set()

            for tx in transactions:
                from_wallet, to_wallet = get_wallet_from_transaction(tx)
                if from_wallet and from_wallet not in seen_wallets:
                    new_wallets.add(from_wallet)
                if to_wallet and to_wallet not in seen_wallets:
                    new_wallets.add(to_wallet)

            if new_wallets:
                update_database_with_wallets(new_wallets)
                seen_wallets.update(new_wallets)
                print(f"Added {len(new_wallets)} new wallets to the database.")

                for wallet in new_wallets:
                    balance = get_balance(wallet)
                    update_balance(wallet, balance)
                    
                    erc20_tokens = fetch_erc20_tokens(wallet)
                    update_erc20_tokens(wallet, erc20_tokens)
                    
                    nfts = fetch_nfts(wallet)
                    update_nfts(wallet, nfts)

            # Wait for 5 minutes
            time.sleep(300)

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
