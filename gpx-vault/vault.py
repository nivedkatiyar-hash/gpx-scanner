#!/usr/bin/env python3
"""
gpx-vault: A secure credential protector with brute-force lockout.
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import argparse
import time
from pathlib import Path

# Paths
VAULT_FILE = Path.home() / ".local" / "share" / "gpx" / "vault.json"

# Lockout Settings
MAX_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # 5 minutes in seconds

# UI Colors
C_GREEN = "\033[92m"
C_BLUE = "\033[94m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_RESET = "\033[0m"

def derive_key(password: str, salt: bytes) -> bytes:
    """Hashes the password 100,000 times to create a secure 256-bit key."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def xor_encrypt_decrypt(data: bytes, key: bytes) -> bytes:
    """A lightweight XOR cipher to scramble the data using the hashed key."""
    stretched_key = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, stretched_key))

def load_vault():
    if not VAULT_FILE.exists():
        return None
    with open(VAULT_FILE, 'r') as f:
        return json.load(f)

def save_vault(salt: bytes, master_hash: bytes, encrypted_data: bytes):
    """Saves the encrypted vault to disk and resets lockout counters."""
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT_FILE, 'w') as f:
        json.dump({
            "salt": base64.b64encode(salt).decode(),
            "master_hash": base64.b64encode(master_hash).decode(),
            "data": base64.b64encode(encrypted_data).decode(),
            "failed_attempts": 0,
            "lockout_until": 0
        }, f, indent=4)

def update_lockout(vault_data, failed_attempts, lockout_until):
    """Updates only the lockout fields without modifying the encrypted data."""
    vault_data["failed_attempts"] = failed_attempts
    vault_data["lockout_until"] = lockout_until
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault_data, f, indent=4)

def unlock_vault():
    """Handles decryption, password prompting, and lockout logic."""
    vault = load_vault()
    if not vault:
        print(f"{C_RED}No vault found. Please run 'setup' first.{C_RESET}")
        sys.exit(1)

    # --- Lockout Check ---
    failed_attempts = vault.get("failed_attempts", 0)
    lockout_until = vault.get("lockout_until", 0)
    current_time = time.time()

    if current_time < lockout_until:
        remaining = int((lockout_until - current_time) / 60)
        print(f"{C_RED}🔒 Vault is locked due to multiple failed attempts.{C_RESET}")
        print(f"{C_YELLOW}Please try again in {remaining} minute(s).{C_RESET}")
        sys.exit(1)

    # --- Prompt for Password ---
    salt = base64.b64decode(vault["salt"])
    master_hash = base64.b64decode(vault["master_hash"])
    
    password = getpass.getpass(f"{C_BLUE}Enter Master Password: {C_RESET}")
    key = derive_key(password, salt)
    
    # --- Verify Password ---
    if hashlib.sha256(key).digest() != master_hash:
        failed_attempts += 1
        
        if failed_attempts >= MAX_ATTEMPTS:
            lockout_until = current_time + LOCKOUT_DURATION
            update_lockout(vault, failed_attempts, lockout_until)
            print(f"{C_RED}✖ {MAX_ATTEMPTS} failed attempts! Vault locked for 5 minutes.{C_RESET}")
        else:
            update_lockout(vault, failed_attempts, lockout_until)
            attempts_left = MAX_ATTEMPTS - failed_attempts
            print(f"{C_RED}✖ Incorrect Password! ({attempts_left} attempts remaining){C_RESET}")
            
        sys.exit(1)

    # --- Success: Reset Lockout and Return Data ---
    if failed_attempts > 0:
        update_lockout(vault, 0, 0)

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
    
    empty_vault_data = json.dumps({}).encode()
    encrypted_data = xor_encrypt_decrypt(empty_vault_data, key)
    
    save_vault(salt, master_hash, encrypted_data)
    print(f"{C_GREEN}✔ Vault securely created!{C_RESET}")

def store_cred(service, username):
    key, salt, master_hash, vault_data = unlock_vault()
    
    password = getpass.getpass(f"Enter password for {service}: ")
    vault_data[service] = {"username": username, "password": password}
    
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
    add_parser.add_argument("service", help="Name of the service")
    add_parser.add_argument("username", help="The username or email")
    
    get_parser = subparsers.add_parser("get", help="Retrieve a credential")
    get_parser.add_argument("service", help="Name of the service")

    args = parser.parse_args()

    if args.command == "setup": setup()
    elif args.command == "add": store_cred(args.service, args.username)
    elif args.command == "get": retrieve_cred(args.service)

if __name__ == "__main__":
    main()
