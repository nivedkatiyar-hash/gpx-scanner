#!/usr/bin/env python3
"""
gpx-vault: Offline credential manager with Envelope Encryption & Recovery Key.
"""

import os
import sys
import json
import base64
import hashlib
import getpass
import argparse
import secrets
from pathlib import Path

VAULT_FILE = Path.home() / ".local" / "share" / "gpx" / "vault.json"

# UI Colors
C_GREEN = "\033[92m"
C_BLUE = "\033[94m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_RESET = "\033[0m"

# --- CRYPTO HELPERS ---

def derive_key(secret: str, salt: bytes) -> bytes:
    """Hashes the secret 100,000 times to create a secure key."""
    return hashlib.pbkdf2_hmac('sha256', secret.encode(), salt, 100000)

def xor_cipher(data: bytes, key: bytes) -> bytes:
    """Symmetric XOR cipher. Used for both encryption and decryption."""
    stretched_key = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, stretched_key))

def b64_enc(data: bytes) -> str: return base64.b64encode(data).decode()
def b64_dec(data: str) -> bytes: return base64.b64decode(data)

# --- VAULT OPERATIONS ---

def load_vault():
    if not VAULT_FILE.exists():
        print(f"{C_RED}No vault found. Run 'setup' first.{C_RESET}")
        sys.exit(1)
    with open(VAULT_FILE, 'r') as f:
        return json.load(f)

def save_vault(data: dict):
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def unlock_vault():
    """Prompts for master password, unwraps the DEK, and decrypts the vault data."""
    v = load_vault()
    
    password = getpass.getpass(f"{C_BLUE}Enter Master Password: {C_RESET}")
    salt_pw = b64_dec(v["salt_pw"])
    pw_hash = b64_dec(v["pw_hash"])
    
    key_pw = derive_key(password, salt_pw)
    
    # Verify password before attempting decryption
    if hashlib.sha256(key_pw).digest() != pw_hash:
        print(f"{C_RED}✖ Incorrect Master Password!{C_RESET}")
        sys.exit(1)

    # Unwrap the Data Encryption Key (DEK)
    enc_dek_pw = b64_dec(v["enc_dek_pw"])
    dek = xor_cipher(enc_dek_pw, key_pw)
    
    # Decrypt actual vault data using the DEK
    encrypted_data = b64_dec(v["data"])
    decrypted_json = xor_cipher(encrypted_data, dek).decode()
    return dek, json.loads(decrypted_json), v

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

    # 1. Generate the master Data Encryption Key (DEK)
    dek = os.urandom(32)
    
    # 2. Setup Master Password
    salt_pw = os.urandom(16)
    key_pw = derive_key(pw1, salt_pw)
    pw_hash = hashlib.sha256(key_pw).digest()
    enc_dek_pw = xor_cipher(dek, key_pw) # Wrap DEK with Password
    
    # 3. Setup Recovery Key
    recovery_code = secrets.token_urlsafe(16) # Looks like: abc123XYZ-_789
    salt_rec = os.urandom(16)
    key_rec = derive_key(recovery_code, salt_rec)
    rec_hash = hashlib.sha256(key_rec).digest()
    enc_dek_rec = xor_cipher(dek, key_rec) # Wrap DEK with Recovery Key
    
    # 4. Encrypt empty data with DEK
    empty_data = json.dumps({}).encode()
    enc_data = xor_cipher(empty_data, dek)
    
    save_vault({
        "salt_pw": b64_enc(salt_pw),
        "pw_hash": b64_enc(pw_hash),
        "enc_dek_pw": b64_enc(enc_dek_pw),
        
        "salt_rec": b64_enc(salt_rec),
        "rec_hash": b64_enc(rec_hash),
        "enc_dek_rec": b64_enc(enc_dek_rec),
        
        "data": b64_enc(enc_data)
    })
    
    print(f"\n{C_GREEN}✔ Vault securely created!{C_RESET}")
    print(f"{C_RED}!!! IMPORTANT: SAVE THIS RECOVERY KEY !!!{C_RESET}")
    print(f"If you lose your password, you will need this exact code:")
    print(f"\n    {C_YELLOW}{recovery_code}{C_RESET}\n")
    print(f"{C_RED}Write it down. It will never be shown again.{C_RESET}")

def recover():
    v = load_vault()
    print(f"{C_BLUE}--- Emergency Vault Recovery ---{C_RESET}")
    rec_input = input("Enter your 16-character Recovery Key: ").strip()
    
    salt_rec = b64_dec(v["salt_rec"])
    rec_hash = b64_dec(v["rec_hash"])
    
    key_rec = derive_key(rec_input, salt_rec)
    
    # Verify Recovery Key
    if hashlib.sha256(key_rec).digest() != rec_hash:
        print(f"{C_RED}✖ Invalid Recovery Key.{C_RESET}")
        sys.exit(1)
        
    print(f"{C_GREEN}✔ Recovery Key Accepted!{C_RESET}\n")
    
    # Unwrap DEK using Recovery Key
    enc_dek_rec = b64_dec(v["enc_dek_rec"])
    dek = xor_cipher(enc_dek_rec, key_rec)
    
    # Create new Master Password
    pw1 = getpass.getpass("Create NEW Master Password: ")
    pw2 = getpass.getpass("Confirm NEW Master Password: ")
    if pw1 != pw2:
        print(f"{C_RED}Passwords do not match. Run recover again.{C_RESET}")
        sys.exit(1)
        
    # Wrap the DEK with the new password
    salt_pw = os.urandom(16)
    key_pw = derive_key(pw1, salt_pw)
    
    v["salt_pw"] = b64_enc(salt_pw)
    v["pw_hash"] = b64_enc(hashlib.sha256(key_pw).digest())
    v["enc_dek_pw"] = b64_enc(xor_cipher(dek, key_pw))
    
    save_vault(v)
    print(f"{C_GREEN}✔ Vault recovered. You may now use your new Master Password.{C_RESET}")

def store_cred(service, username):
    dek, vault_data, v = unlock_vault()
    password = getpass.getpass(f"Enter password for {service}: ")
    vault_data[service] = {"username": username, "password": password}
    
    v["data"] = b64_enc(xor_cipher(json.dumps(vault_data).encode(), dek))
    save_vault(v)
    print(f"{C_GREEN}✔ Credential securely stored.{C_RESET}")

def retrieve_cred(service):
    dek, vault_data, _ = unlock_vault()
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
    subparsers.add_parser("recover", help="Reset a forgotten master password")
    
    add_parser = subparsers.add_parser("add", help="Store a new credential")
    add_parser.add_argument("service", help="Name of the service")
    add_parser.add_argument("username", help="The username or email")
    
    get_parser = subparsers.add_parser("get", help="Retrieve a credential")
    get_parser.add_argument("service", help="Name of the service")

    args = parser.parse_args()

    if args.command == "setup": setup()
    elif args.command == "recover": recover()
    elif args.command == "add": store_cred(args.service, args.username)
    elif args.command == "get": retrieve_cred(args.service)

if __name__ == "__main__":
    main()
