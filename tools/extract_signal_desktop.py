"""
Extract messages from Signal Desktop's SQLCipher database.
Decrypts the key using Windows DPAPI, then reads messages via sqlcipher.
"""
import ctypes
import ctypes.wintypes
import json
import os
import re
import shutil
import sqlite3


def _safe_ident(name: str) -> str:
    """Validate SQL identifier to prevent injection."""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _validate_hex_key(key: str) -> str:
    """Validate that an encryption key is hex-only."""
    if not key or not re.match(r'^[0-9a-fA-F]+$', key):
        raise ValueError("Invalid encryption key format — expected hex string")
    return key

# --- Step 1: Decrypt the database key using DPAPI ---

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_char))
    ]

def decrypt_dpapi(encrypted_bytes):
    blob_in = DATA_BLOB()
    blob_in.cbData = len(encrypted_bytes)
    blob_in.pbData = ctypes.create_string_buffer(encrypted_bytes, len(encrypted_bytes))

    blob_out = DATA_BLOB()

    result = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out)
    )

    if not result:
        raise RuntimeError(f"DPAPI decryption failed. Error: {ctypes.GetLastError()}")

    decrypted = ctypes.string_at(blob_out.pbData, blob_out.cbData)
    ctypes.windll.kernel32.LocalFree(blob_out.pbData)
    return decrypted

def get_signal_key():
    config_path = os.path.join(os.environ['APPDATA'], 'Signal', 'config.json')
    with open(config_path) as f:
        config = json.load(f)

    enc_hex = config['encryptedKey']
    enc_bytes = bytes.fromhex(enc_hex)
    dec_bytes = decrypt_dpapi(enc_bytes)
    return dec_bytes.hex()

# --- Step 2: Copy and read the database ---

def copy_signal_db(dest_dir):
    """Copy the Signal Desktop database to our working directory."""
    src = os.path.join(os.environ['APPDATA'], 'Signal', 'sql', 'db.sqlite')
    dest = os.path.join(dest_dir, 'signal_desktop.sqlite')

    if not os.path.exists(src):
        raise FileNotFoundError(f"Signal Desktop database not found at {src}")

    print(f"Copying Signal Desktop database ({os.path.getsize(src) / 1024 / 1024:.1f} MB)...")
    shutil.copy2(src, dest)
    print(f"Copied to {dest}")
    return dest

def read_signal_desktop_plain(db_path, key_hex):
    """
    Signal Desktop uses SQLCipher. We can't read it with plain sqlite3.
    Instead, let's try using the key to decrypt via sqlcipher if available,
    or fall back to examining what we can.
    """
    # First, let's just check if the file is actually encrypted
    with open(db_path, 'rb') as f:
        header = f.read(16)

    if header[:6] == b'SQLite':
        print("Database is NOT encrypted (plain SQLite). Reading directly...")
        return read_plain_sqlite(db_path)
    print(f"Database is encrypted (header: {header[:16].hex()})")
    print("Need sqlcipher to decrypt. Checking availability...")
    return None

def read_plain_sqlite(db_path):
    """Read messages from a plain (unencrypted) SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables found: {len(tables)}")
    for t in tables:
        try:
            safe_t = _safe_ident(t)
            cursor.execute(f"SELECT COUNT(*) FROM [{safe_t}]")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  {t}: {count} rows")
        except ValueError:
            print(f"  {t}: skipped (invalid name)")

    conn.close()
    return tables

def try_sqlcipher(db_path, key_hex):
    """Try to use pysqlcipher3 to read the encrypted database."""
    try:
        key_hex = _validate_hex_key(key_hex)
        from pysqlcipher3 import dbapi2 as sqlcipher
        conn = sqlcipher.connect(db_path)
        conn.execute(f"PRAGMA key=\"x'{key_hex}'\"")
        conn.execute("PRAGMA cipher_compatibility = 4")

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"SQLCipher tables found: {len(tables)}")

        conn.close()
        return True
    except ImportError:
        print("pysqlcipher3 not installed")
        return False
    except Exception as e:
        print(f"SQLCipher error: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract messages from Signal Desktop')
    parser.add_argument('--output-dir', default='.', help='Directory to save output')
    parser.add_argument('--save-key', action='store_true', help='Save the decrypted key to a file (WARNING: insecure)')
    args = parser.parse_args()
    base_dir = args.output_dir

    print("=== Signal Desktop Message Extractor ===\n")

    # Step 1: Get the key
    print("Step 1: Extracting database key via DPAPI...")
    try:
        key = get_signal_key()
        print(f"Key extracted successfully ({len(key)} hex chars)")
    except Exception as e:
        print(f"Failed to extract key: {e}")
        return

    # Step 2: Copy the database
    print("\nStep 2: Copying Signal Desktop database...")
    try:
        db_path = copy_signal_db(base_dir)
    except Exception as e:
        print(f"Failed to copy database: {e}")
        return

    # Step 3: Try to read it
    print("\nStep 3: Attempting to read database...")
    result = read_signal_desktop_plain(db_path, key)

    if result is None:
        # Database is encrypted, need sqlcipher
        print("\nThe database is encrypted with SQLCipher.")
        print("Options:")
        print("  1. Install pysqlcipher3: pip install pysqlcipher3")
        print("  2. Use sqlcipher CLI tool")
        print("  3. Use Signal's built-in export (if available)")
        print(f"\nKey length: {len(key)} hex chars")
        # NOTE: Key value is NOT printed to stdout for security

        if args.save_key:
            # Save key for other tools (in the output directory, not a hardcoded path)
            key_file = os.path.join(base_dir, 'signal_desktop_key.txt')
            with open(key_file, 'w') as f:
                f.write(key)
            print(f"Key saved to {key_file}")
        else:
            print("Key extracted but NOT saved to disk (use --save-key to save).")

        # Try sqlcipher
        print("\nTrying pysqlcipher3...")
        try_sqlcipher(db_path, key)

if __name__ == '__main__':
    main()
