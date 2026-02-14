"""
Extract messages from Signal Desktop's SQLCipher database.
"""
import argparse
import re


def _validate_hex_key(key: str) -> str:
    if not key or not re.match(r'^[0-9a-fA-F]+$', key):
        raise ValueError("Invalid encryption key format")
    return key


def _safe_ident(name: str) -> str:
    """Validate SQL identifier to prevent injection."""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


parser = argparse.ArgumentParser(description='Read Signal Desktop encrypted database')
parser.add_argument('--key-file', required=True, help='Path to key file')
parser.add_argument('--db-path', required=True, help='Path to Signal Desktop database')
args = parser.parse_args()

with open(args.key_file) as f:
    db_key = _validate_hex_key(f.read().strip())

db_path = args.db_path

print(f"Opening database: {db_path}")
print(f"Key length: {len(db_key)} chars")

import sqlcipher3

conn = sqlcipher3.connect(db_path)
cursor = conn.cursor()

# Set the key
cursor.execute(f"PRAGMA key=\"x'{db_key}'\"")
# Signal Desktop uses SQLCipher 4 defaults
cursor.execute("PRAGMA cipher_compatibility = 4")

# Test: list tables
print("\n=== Tables ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for t in tables:
    name = t[0]
    try:
        safe_name = _safe_ident(name)
        cursor.execute(f"SELECT COUNT(*) FROM [{safe_name}]")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  {name}: {count:,} rows")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

conn.close()
