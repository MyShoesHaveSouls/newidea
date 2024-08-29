import time
import sqlite3
import requests
import asyncio
import aiohttp
from aiohttp import ClientSession
from asyncio import Semaphore
from random import choice

ETHERSCAN_API_KEYS = [
    'F92Z14GE2DTF6PBBYY1YPHPJ438PT3P2VI',
    '4Q5U7HNF4CGTVTGEMGRV5ZU9WYNJ6N7YA5',
    'EX8K12JY7BCVG8RAUU8X2Z6QT2GCF5EYB4',
    'DZHWCIEA2WW86CZEC88IGWG1JFB6JN3VHS',
    'YIDAXPUWHJB21RJVMS1JMXHABMEF67RQWG',
    '12RU83G1ATVA9V4EMM3U45X8BG4RG9PM6T',
    'PYM9U2QD949KZZX23QJ4YZRX3KC3PHAI88',
    'SH884AZJMKIFDMAPSMHTHJUQ3QIRPH827I',
    'PYM9U2QD949KZZX23QJ4YZRX3KC3PHAI88',
    'TDMPDZU8RD4V9FVB66P5S47QETEJ6R61UY'
]

ETHERSCAN_API_URL = 'https://api.etherscan.io/api'
DATABASE_FILE = 'database.db'
MAX_CALLS_PER_SECOND = 5  # Limit to 5 API calls per second per API key

# Create a semaphore for each API key
semaphores = {key: Semaphore(MAX_CALLS_PER_SECOND) for key in ETHERSCAN_API_KEYS}

def initialize_database():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY
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

async def fetch_with_rate_limit(session: ClientSession, url: str, params: dict, api_key: str):
    async with semaphores[api_key]:  # Semaphore for the specific API key
        async with session.get(url, params=params) as response:
            await asyncio.sleep(1)  # Ensure the rate limit of 5 calls per second per key
            return await response.json()

async def get_recent_transactions(session: ClientSession):
    api_key = choice(ETHERSCAN_API_KEYS)  # Select a random API key for each call
    params = {
        'module': 'proxy',
        'action': 'eth_getBlockByNumber',
        'tag': 'latest',
        'boolean': 'true',
        'apikey': api_key
    }
    data = await fetch_with_rate_limit(session, ETHERSCAN_API_URL, params, api_key)

    if data['status'] == '1' and 'result' in data:
        return data['result']['transactions']
    else:
        print(f"Error fetching transactions: {data.get('result', 'Unknown error')}")
        return []

def get_wallet_from_transaction(transaction):
    from_wallet = transaction['from']
    to_wallet = transaction['to']
    return from_wallet, to_wallet

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

async def fetch_erc20_tokens(session: ClientSession, address):
    api_key = choice(ETHERSCAN_API_KEYS)  # Select a random API key for each call
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
            'apikey': api_key
        }
        data = await fetch_with_rate_limit(session, ETHERSCAN_API_URL, params, api_key)

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

async def fetch_nfts(session: ClientSession, address):
    opensea_url = f'https://api.opensea.io/api/v1/assets?owner={address}&order_direction=desc&offset=0&limit=50'
    async with session.get(opensea_url) as response:
        data = await response.json()

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

async def main():
    initialize_database()
    seen_wallets = set()

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                transactions = await get_recent_transactions(session)
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

                    tasks = []
                    for wallet in new_wallets:
                        tasks.append(fetch_erc20_tokens(session, wallet))
                        tasks.append(fetch_nfts(session, wallet))

                    results = await asyncio.gather(*tasks)
                    for wallet, (erc20_tokens, nfts) in zip(new_wallets, zip(results[::2], results[1::2])):
                        update_erc20_tokens(wallet, erc20_tokens)
                        update_nfts(wallet, nfts)

                # Wait for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
