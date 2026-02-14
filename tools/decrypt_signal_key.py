"""
Decrypt Signal Desktop database key using Chromium's os_crypt method.
1. Get master key from Local State (DPAPI encrypted)
2. Use master key to AES-GCM decrypt the "v10" encrypted config key
3. Use the config key to open the SQLCipher database
"""
import base64
import ctypes
import ctypes.wintypes
import json
import os


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def dpapi_decrypt(encrypted_bytes):
    blob_in = DATA_BLOB(len(encrypted_bytes), ctypes.create_string_buffer(encrypted_bytes, len(encrypted_bytes)))
    blob_out = DATA_BLOB()
    result = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    )
    if not result:
        raise RuntimeError(f"DPAPI failed, error {ctypes.GetLastError()}")
    dec = ctypes.string_at(blob_out.pbData, blob_out.cbData)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    return dec

def get_master_key():
    """Get the Chromium os_crypt master key from Local State."""
    local_state_path = os.path.join(os.environ['APPDATA'], 'Signal', 'Local State')
    with open(local_state_path) as f:
        local_state = json.load(f)

    encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
    encrypted_key = base64.b64decode(encrypted_key_b64)

    # Strip "DPAPI" prefix (5 bytes)
    if encrypted_key[:5] == b'DPAPI':
        encrypted_key = encrypted_key[5:]

    master_key = dpapi_decrypt(encrypted_key)
    print(f"Master key extracted: {len(master_key)} bytes")
    return master_key

def decrypt_v10(encrypted_value, master_key):
    """Decrypt a v10-prefixed value using AES-256-GCM with the master key."""
    from Crypto.Cipher import AES

    # v10 format: "v10" (3 bytes) + nonce (12 bytes) + ciphertext+tag
    nonce = encrypted_value[3:15]
    ciphertext_tag = encrypted_value[15:]
    ciphertext = ciphertext_tag[:-16]
    tag = ciphertext_tag[-16:]

    cipher = AES.new(master_key, AES.MODE_GCM, nonce=nonce)
    decrypted = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted

def main():
    signal_dir = os.path.join(os.environ['APPDATA'], 'Signal')

    print("=== Signal Desktop Key Decryption ===\n")

    # Step 1: Get master key from Local State
    print("Step 1: Extracting master key from Local State (DPAPI)...")
    master_key = get_master_key()

    # Step 2: Decrypt the config key
    print("\nStep 2: Decrypting config key (AES-GCM with v10 prefix)...")
    with open(os.path.join(signal_dir, 'config.json')) as f:
        config = json.load(f)

    enc_key_hex = config['encryptedKey']
    enc_key_bytes = bytes.fromhex(enc_key_hex)

    if enc_key_bytes[:3] == b'v10':
        db_key = decrypt_v10(enc_key_bytes, master_key)
        db_key_hex = db_key.decode('utf-8') if all(32 <= b < 127 for b in db_key) else db_key.hex()
        print(f"Database key decrypted: {len(db_key)} bytes")
    else:
        print("Key doesn't have v10 prefix, trying raw DPAPI...")
        db_key = dpapi_decrypt(enc_key_bytes)
        db_key_hex = db_key.hex()

    # Save the key to a user-specified or default location
    import argparse
    parser = argparse.ArgumentParser(description='Decrypt Signal Desktop database key')
    parser.add_argument('--output-dir', default='.', help='Directory to save the key file')
    args = parser.parse_args()

    key_file = os.path.join(args.output_dir, "signal_desktop_key.txt")
    os.makedirs(args.output_dir, exist_ok=True)
    with open(key_file, 'w') as f:
        f.write(db_key_hex)
    print(f"Key saved to {key_file}")
    # NOTE: Key value is NOT printed to stdout for security

    # Step 3: Try to open the database
    print("\nStep 3: Testing database access...")
    db_path = os.path.join(os.environ.get('APPDATA', ''), 'Signal', 'sql', 'db.sqlite')

    # Try with sqlcipher via subprocess
    # For now, just confirm we have the key
    print(f"\nDatabase: {db_path}")
    print(f"Key length: {len(db_key_hex)} hex chars")
    print("\nTo open with sqlcipher CLI:")
    print(f'  sqlcipher "{db_path}"')
    print("  PRAGMA key=\"x'<KEY>'\";")
    print("  .tables")

if __name__ == '__main__':
    main()
