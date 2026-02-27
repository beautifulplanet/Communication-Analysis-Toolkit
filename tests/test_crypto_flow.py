import os
import sys

sys.path.append(os.getcwd())

import json

from cryptography.fernet import Fernet

# Generate a key
key = Fernet.generate_key().decode()
os.environ["ENCRYPTION_KEY"] = key

# Import after setting env
from api.config import get_settings  # noqa: E402

# Clear cache just in case
get_settings.cache_clear()

from engine.crypto import decrypt_data, encrypt_data, get_cipher_suite  # noqa: E402


def test_crypto():
    print(f"Key: {key}")
    settings = get_settings()
    print(f"Settings Key: {settings.encryption_key}")

    if not get_cipher_suite():
        print("ERROR: Cipher suite not initialized!")
        return

    original = b"Secret Message"
    encrypted = encrypt_data(original)

    print(f"Original: {original}")
    print(f"Encrypted: {encrypted}")

    if original == encrypted:
        print("ERROR: Data was not encrypted!")
        return

    decrypted = decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")

    if original != decrypted:
        print("ERROR: Decryption failed!")
    else:
        print("SUCCESS: Encryption/Decryption round trip works.")

    # Test JSON logic
    data = {"foo": "bar"}
    json_bytes = json.dumps(data).encode("utf-8")
    enc_json = encrypt_data(json_bytes)
    dec_json = decrypt_data(enc_json)
    loaded = json.loads(dec_json)
    print(f"JSON Round Trip: {loaded}")

if __name__ == "__main__":
    test_crypto()
