"""
Deploy BimaRegistry.sol to the Polygon Amoy testnet.

Run this ONCE from the repo root, outside of the Django request cycle:

    pip install py-solc-x --break-system-packages   # if not already installed
    python scripts/deploy_registry.py

Requires, in your .env (or exported in the shell):
    POLYGON_AMOY_RPC_URL   — e.g. an Alchemy Amoy endpoint
    OPERATOR_PRIVATE_KEY   — private key of a wallet funded with test POL
                              (get free POL: https://www.alchemy.com/faucets/polygon-amoy)

On success this prints the deployed contract address — copy that into
BIMA_BORA_REGISTRY_ADDRESS in your .env file. It also overwrites
apps/audit/contracts/bima_registry_abi.json with the freshly compiled ABI,
so re-run this after any change to BimaRegistry.sol.
"""

import json
import os
import sys
from pathlib import Path

from decouple import config
from solcx import compile_standard, install_solc, set_solc_version
from web3 import Web3

BASE_DIR = Path(__file__).resolve().parent.parent
CONTRACT_PATH = BASE_DIR / 'apps' / 'audit' / 'contracts' / 'BimaRegistry.sol'
ABI_OUTPUT_PATH = BASE_DIR / 'apps' / 'audit' / 'contracts' / 'bima_registry_abi.json'

SOLC_VERSION = '0.8.20'


def compile_contract() -> tuple[list, str]:
    print(f'Compiling {CONTRACT_PATH.name}...')
    source = CONTRACT_PATH.read_text()

    install_solc(SOLC_VERSION)
    set_solc_version(SOLC_VERSION)

    compiled = compile_standard({
        'language': 'Solidity',
        'sources': {'BimaRegistry.sol': {'content': source}},
        'settings': {'outputSelection': {'*': {'*': ['abi', 'evm.bytecode']}}},
    })

    contract_data = compiled['contracts']['BimaRegistry.sol']['BimaRegistry']
    abi = contract_data['abi']
    bytecode = contract_data['evm']['bytecode']['object']
    print('Compilation successful.')
    return abi, bytecode


def main():
    rpc_url = config('POLYGON_AMOY_RPC_URL', default='https://rpc-amoy.polygon.technology')
    private_key = config('OPERATOR_PRIVATE_KEY', default='')

    if not private_key:
        print('ERROR: OPERATOR_PRIVATE_KEY is not set in your .env file.')
        sys.exit(1)

    abi, bytecode = compile_contract()

    ABI_OUTPUT_PATH.write_text(json.dumps(abi, indent=2))
    print(f'ABI written to {ABI_OUTPUT_PATH}')

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    try:
        from web3.middleware import geth_poa_middleware
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except ImportError:
        pass

    try:
        account = w3.eth.account.from_key(private_key)
    except Exception:
        print('ERROR: OPERATOR_PRIVATE_KEY is not a valid 64-character hex private key.')
        sys.exit(1)

    print(f'Deploying from address: {account.address}')
    balance = w3.eth.get_balance(account.address)
    print(f'Account balance: {w3.from_wei(balance, "ether")} POL')

    if balance == 0:
        print('ERROR: Account balance is 0. Fund it at https://www.alchemy.com/faucets/polygon-amoy')
        sys.exit(1)

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = contract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2_000_000,
        'gasPrice': w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    raw = getattr(signed, 'raw_transaction', None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    print('Waiting for deployment transaction to confirm...')
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    print('\n=========================================')
    print('BimaRegistry deployed successfully!')
    print(f'Contract Address: {receipt.contractAddress}')
    print('=========================================')
    print('Copy this into BIMA_BORA_REGISTRY_ADDRESS in your .env file.')


if __name__ == '__main__':
    main()
