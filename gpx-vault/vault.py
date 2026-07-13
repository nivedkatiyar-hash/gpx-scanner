#!/usr/bin/env python3
"""
gpx-vault: A secure credential protector and local password manager.
Uses standard Python libraries to hash a master password and encrypt credentials.
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import argparse
from pathlib import Path

# Paths
VAULT_FILE = Path.home() / ".local" / "share" / "gpx" / "vault.json"

# UI Colors
C_GREEN = "\033[92m"
C_BLUE = "\033[94m"
C_RED = "\033[91m"
C_RESET = "\033[0m"

def derive_key(password: str, salt: bytes) -> bytes:
    """Hashes the password 100,000 times to create a secure 256-bit key."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def xor_encrypt_decrypt(data: bytes, key: bytes) -> bytes:
    """A lightweight XOR cipher to scramble the data using the hashed key."""
    # Stretch the key to match the length of the data
    stretched_key = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, stretched_key))

def load_vault():
    """Loads the vault file if it exists, otherwise returns an empty structure."""
    if not VAULT_FILE.exists():
        return None
    with open(VAULT_FILE, 'r') as f:
        return json.load(f)

def save_vault(salt: bytes, master_hash: bytes, encrypted_data: bytes):
    """Saves the encrypted vault to disk."""
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT_FILE, 'w') as f:
        json.dump({
            "salt": base64.b64encode(salt).decode(),
            "master_hash": base64.b64encode(master_hash).decode(),
            "data": base64.b64encode(encrypted_data).decode()
        }, f, indent=4)

def unlock_vault():
    """Prompts for the master password and decrypts the vault."""
    vault = load_vault()
    if not vault:
        print(f"{C_RED}No vault found. Please run 'setup' first.{C_RESET}")
        sys.exit(1)

    salt = base64.b64decode(vault["salt"])
    master_hash = base64.b64decode(vault["master_hash"])
    
    # Securely ask for password
    password = getpass.getpass(f"{C_BLUE}Enter Master Password: {C_RESET}")
    
    # Verify password
    key = derive_key(password, salt)
    if hashlib.sha256(key).digest() != master_hash:
        print(f"{C_RED}✖ Incorrect Master Password!{C_RESET}")
        sys.exit(1)

    # Decrypt data
    encrypted_data = base64.b64decode(vault["data"])
    decrypted_json = xor_encrypt_decrypt(encrypted_data, key).decode()
    return key, salt, master_hash, json.loads(decrypted_json)

# --- COMMANDS ---

def setup():
    if VAULT_FILE.exists():
        print(f"{C_RED}Vault already exists!{C_RESET}")
        sys.exit(1)
        
    print(f"{C_BLUE}--- Create your gpx-vault ---{C_RESET}")
    pw1 = getpass.getpass("Create Master Password: ")
    pw2 = getpass.getpass("Confirm Master Password: ")
    
    if pw1 != pw2:
        print(f"{C_RED}Passwords do not match.{C_RESET}")
        sys.exit(1)
        
    salt = os.urandom(16)
    key = derive_key(pw1, salt)
    master_hash = hashlib.sha256(key).digest()
    
    # Start with an empty dictionary
    empty_vault_data = json.dumps({}).encode()
    encrypted_data = xor_encrypt_decrypt(empty_vault_data, key)
    
    save_vault(salt, master_hash, encrypted_data)
    print(f"{C_GREEN}✔ Vault securely created!{C_RESET}")

def store_cred(service, username):
    key, salt, master_hash, vault_data = unlock_vault()
    
    password = getpass.getpass(f"Enter password for {service}: ")
    
    vault_data[service] = {"username": username, "password": password}
    
    # Re-encrypt and save
    encrypted_data = xor_encrypt_decrypt(json.dumps(vault_data).encode(), key)
    save_vault(salt, master_hash, encrypted_data)
    print(f"{C_GREEN}✔ Credential securely stored.{C_RESET}")

def retrieve_cred(service):
    _, _, _, vault_data = unlock_vault()
    
    if service in vault_data:
        print(f"\n{C_BLUE}--- {service} ---{C_RESET}")
        print(f"Username: {vault_data[service]['username']}")
        print(f"Password: {vault_data[service]['password']}")
    else:
        print(f"{C_RED}✖ No credentials found for '{service}'{C_RESET}")

def main():
    parser = argparse.ArgumentParser(description="gpx-vault: Secure Credential Storage")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup", help="Initialize the secure vault")
    
    add_parser = subparsers.add_parser("add", help="Store a new credential")
    add_parser.add_argument("service", help="Name of the service (e.g. github, aws)")
    add_parser.add_argument("username", help="The username or email")
    
    get_parser = subparsers.add_parser("get", help="Retrieve a credential")
    get_parser.add_argument("service", help="Name of the service")

    args = parser.parse_args()

    if args.command == "setup": setup()
    elif args.command == "add": store_cred(args.service, args.username)
    elif args.command == "get": retrieve_cred(args.service)

if __name__ == "__main__":
    main()
