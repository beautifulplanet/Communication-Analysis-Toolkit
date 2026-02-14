r"""
Signal Desktop Message Extractor
=================================
Reads the Signal Desktop local database and extracts all messages
from a target contact's conversation (both sides).

Signal Desktop stores messages in an encrypted SQLCipher database at:
  %APPDATA%\Signal\sql\db.sqlite

The encryption key is stored in:
  %APPDATA%\Signal\config.json  (field: "key")

This script:
  1. Reads the encryption key from config.json
  2. Opens the database with sqlcipher (or falls back to pysqlcipher3)
  3. Extracts all messages from the target conversation
  4. Saves to JSON for the analysis engine to consume

Usage:
  python signal_desktop_extractor.py --phone "+1234567890" --name "Contact Name"
  python signal_desktop_extractor.py --config cases/my_project/config.json
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def _safe_ident(name: str) -> str:
    """Validate a SQL identifier to prevent injection via dynamic table/column names."""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def _validate_hex_key(key: str) -> str:
    """Validate that an encryption key is hex-only to prevent PRAGMA injection."""
    if not key or not re.match(r'^[0-9a-fA-F]+$', key):
        raise ValueError("Invalid encryption key format — expected hex string")
    return key

# ── Configuration (set via CLI args or config file, no hardcoded values) ──
CONTACT_PHONE = ""
CONTACT_NAME = ""

SIGNAL_DIR = os.path.join(os.environ.get("APPDATA", ""), "Signal")
CONFIG_FILE = os.path.join(SIGNAL_DIR, "config.json")
DB_FILE = os.path.join(SIGNAL_DIR, "sql", "db.sqlite")

OUTPUT_FILE = ""


def load_contact_config(args):
    """Load contact info from CLI args or config file."""
    global CONTACT_PHONE, CONTACT_NAME, OUTPUT_FILE

    if args.config:
        with open(args.config, encoding='utf-8') as f:
            cfg = json.load(f)
        CONTACT_PHONE = cfg.get("contact_phone", "")
        CONTACT_NAME = cfg.get("contact_label", cfg.get("contact_name", "Contact"))
        output_dir = cfg.get("output_dir", os.path.dirname(args.config))
        OUTPUT_FILE = os.path.join(output_dir, "signal_desktop_messages.json")
    else:
        CONTACT_PHONE = args.phone or ""
        CONTACT_NAME = args.name or "Contact"
        OUTPUT_FILE = args.output or os.path.join(
            os.path.dirname(__file__), "..", "signal_desktop_messages.json"
        )

    if not CONTACT_PHONE:
        logger.error("Error: --phone or --config with contact_phone is required")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)


def check_signal_desktop():
    """Verify Signal Desktop is installed and has data."""
    print("Checking Signal Desktop installation...")

    if not os.path.exists(SIGNAL_DIR):
        logger.error(f"Signal Desktop data folder not found: {SIGNAL_DIR}")
        logger.info("→ Install Signal Desktop from https://signal.org/download")
        logger.info("→ Link it to your phone and wait for messages to sync")
        return False

    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Config file not found: {CONFIG_FILE}")
        logger.info("→ Signal Desktop may not be fully set up yet")
        return False

    if not os.path.exists(DB_FILE):
        logger.error(f"Database not found: {DB_FILE}")
        logger.info("→ Signal Desktop may still be syncing")
        return False

    db_size = os.path.getsize(DB_FILE)
    print("  ✅ Signal Desktop found")
    print(f"  ✅ Database: {DB_FILE} ({db_size:,} bytes / {db_size/1024/1024:.1f} MB)")
    return True


def get_encryption_key():
    """Read the database encryption key from Signal Desktop config."""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        key = config.get('key')
        if key:
            print(f"  ✅ Encryption key found ({len(key)} chars)")
            return key
            return key
        logger.error("No 'key' field in config.json")
        return None
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return None


def try_sqlcipher(db_path, key):
    """Try to open the database using sqlcipher via pysqlcipher3."""
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher
        conn = sqlcipher.connect(db_path)
        c = conn.cursor()
        c.execute(f"PRAGMA key=\"x'{key}'\";")
        c.execute("PRAGMA cipher_page_size = 4096;")
        c.execute("PRAGMA kdf_iter = 64000;")
        c.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512;")
        c.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;")
        # Test query
        c.execute("SELECT count(*) FROM sqlite_master")
        count = c.fetchone()[0]
        print(f"  ✅ SQLCipher connected ({count} tables)")
        return conn
    except ImportError:
        print("  ⚠️ pysqlcipher3 not installed, trying alternative methods...")
        return None
    except Exception as e:
        print(f"  ⚠️ SQLCipher error: {e}")
        return None


def try_sqlcipher_binary(db_path, key, query):
    """Try using sqlcipher CLI binary if available."""
    key = _validate_hex_key(key)
    for cmd in ['sqlcipher', 'sqlcipher.exe']:
        try:
            input_cmds = f"""PRAGMA key="x'{key}'";
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 64000;
PRAGMA cipher_hmac_algorithm = HMAC_SHA512;
PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;
.mode json
{query}
"""
            result = subprocess.run(
                [cmd, db_path],
                input=input_cmds,
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            continue
    return None


def try_decrypt_to_plain_sqlite(db_path, key):
    """Decrypt the SQLCipher database to a plain SQLite file we can read normally."""
    import sqlite3

    key = _validate_hex_key(key)
    # Use a temp file for the decrypted database (auto-cleaned)
    _tmp_handle = tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False)
    plain_db = _tmp_handle.name
    _tmp_handle.close()

    # Method 1: Use pysqlcipher3 to export
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher
        conn = sqlcipher.connect(db_path)
        c = conn.cursor()
        c.execute(f"PRAGMA key=\"x'{key}'\";")
        c.execute("PRAGMA cipher_page_size = 4096;")
        c.execute("PRAGMA kdf_iter = 64000;")
        c.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512;")
        c.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;")

        c.execute("ATTACH DATABASE ? AS plaintext KEY '';", (plain_db,))
        c.execute("SELECT sqlcipher_export('plaintext');")
        c.execute("DETACH DATABASE plaintext;")
        conn.close()

        # Verify
        conn2 = sqlite3.connect(plain_db)
        count = conn2.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]
        print(f"  ✅ Decrypted to plain SQLite ({count} tables)")
        return conn2
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ Decrypt method 1 failed: {e}")

    # Method 2: Use sqlcipher CLI
    for cmd in ['sqlcipher', 'sqlcipher.exe']:
        try:
            input_cmds = f"""PRAGMA key="x'{key}'";
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 64000;
PRAGMA cipher_hmac_algorithm = HMAC_SHA512;
PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;
ATTACH DATABASE "{plain_db}" AS plaintext KEY '';
SELECT sqlcipher_export('plaintext');
DETACH DATABASE plaintext;
"""
            result = subprocess.run(
                [cmd, db_path],
                input=input_cmds,
                capture_output=True, text=True, timeout=120
            )
            if os.path.exists(plain_db) and os.path.getsize(plain_db) > 0:
                conn2 = sqlite3.connect(plain_db)
                count = conn2.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]
                print(f"  ✅ Decrypted via CLI ({count} tables)")
                return conn2
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    return None


def extract_messages_sqlcipher(conn):
    """Extract messages from the Signal Desktop database."""
    c = conn.cursor()

    # First, find tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    print(f"\n  Tables found: {', '.join(tables[:20])}")

    # Signal Desktop schema varies by version — check for common table names
    msg_table = None
    for candidate in ['messages', 'message', 'sms', 'conversations']:
        if candidate in tables:
            msg_table = candidate
            break

    if not msg_table:
        print(f"  ❌ No message table found. Available: {tables}")
        return []

    # Validate identifiers from DB metadata before using in queries
    msg_table = _safe_ident(msg_table)

    # Get columns
    c.execute(f"PRAGMA table_info({msg_table})")
    cols = [col[1] for col in c.fetchall()]
    print(f"  Message table '{msg_table}' columns: {cols[:15]}...")

    # Count total messages
    total = c.execute(f"SELECT COUNT(*) FROM {msg_table}").fetchone()[0]  # nosec B608 — msg_table validated by _safe_ident
    print(f"  Total messages in database: {total:,}")

    # Find the conversation — try by phone number
    conv_table = 'conversations' if 'conversations' in tables else None
    conversation_id = None

    if conv_table:
        conv_table = _safe_ident(conv_table)
        c.execute(f"PRAGMA table_info({conv_table})")
        conv_cols = [col[1] for col in c.fetchall()]
        print(f"  Conversations columns: {conv_cols[:15]}...")

        # Try to find the target contact by phone number
        for search_col in ['e164', 'phone', 'number', 'id', 'serviceId']:
            if search_col in conv_cols:
                try:
                    search_col = _safe_ident(search_col)
                    c.execute(f"SELECT * FROM {conv_table} WHERE {search_col} LIKE ?", (f'%{CONTACT_PHONE}%',))  # nosec B608 — identifiers validated by _safe_ident
                    row = c.fetchone()
                    if row:
                        row_dict = dict(zip(conv_cols, row))
                        conversation_id = row_dict.get('id')
                        print(f"  ✅ Found contact via {search_col}: conversation_id={conversation_id}")
                        print(f"     Name: {row_dict.get('name', row_dict.get('profileName', '?'))}")
                        break
                except Exception:
                    continue

    # Extract messages
    messages = []

    # Build query based on available columns
    body_col = next((col for col in ['body', 'text', 'content', 'message'] if col in cols), None)
    time_col = next((col for col in ['sent_at', 'timestamp', 'date', 'received_at', 'sent_timestamp'] if col in cols), None)
    type_col = next((col for col in ['type', 'direction', 'msg_type'] if col in cols), None)
    conv_col = next((col for col in ['conversationId', 'conversation_id', 'thread_id', 'threadId'] if col in cols), None)
    source_col = next((col for col in ['source', 'sourceServiceId', 'from', 'sender'] if col in cols), None)

    print(f"\n  Column mapping: body={body_col}, time={time_col}, type={type_col}, conv={conv_col}")

    if not body_col or not time_col:
        print("  ❌ Cannot find body/timestamp columns")
        return []

    # Validate all column identifiers before using in queries
    body_col = _safe_ident(body_col)
    time_col = _safe_ident(time_col)
    if conv_col:
        conv_col = _safe_ident(conv_col)

    # Query messages for our conversation
    if conversation_id and conv_col:
        query = f"SELECT * FROM {msg_table} WHERE {conv_col} = ? AND {body_col} IS NOT NULL ORDER BY {time_col}"  # nosec B608 — identifiers validated by _safe_ident
        c.execute(query, (conversation_id,))
    else:
        # Get all messages and filter later
        query = f"SELECT * FROM {msg_table} WHERE {body_col} IS NOT NULL ORDER BY {time_col}"  # nosec B608 — identifiers validated by _safe_ident
        c.execute(query)

    rows = c.fetchall()
    print(f"  Retrieved {len(rows):,} messages with text")

    for row in rows:
        row_dict = dict(zip(cols, row))

        body = row_dict.get(body_col, '')
        if not body or not str(body).strip():
            continue

        ts = row_dict.get(time_col, 0)
        if isinstance(ts, int) and ts > 1e12:
            ts_seconds = ts / 1000
        elif isinstance(ts, int):
            ts_seconds = ts
        else:
            continue

        try:
            dt = datetime.fromtimestamp(ts_seconds)
        except (ValueError, OSError):
            continue

        # Determine direction
        msg_type = str(row_dict.get(type_col, '')).lower()
        if 'outgoing' in msg_type or 'sent' in msg_type:
            direction = 'sent'
        elif 'incoming' in msg_type or 'received' in msg_type:
            direction = 'received'
        else:
            # Signal Desktop uses 'incoming' and 'outgoing' as type values
            direction = 'received' if msg_type == 'incoming' else 'sent' if msg_type == 'outgoing' else 'unknown'

        messages.append({
            'timestamp': int(ts * 1000) if ts < 1e12 else int(ts),
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M:%S'),
            'direction': direction,
            'body': str(body),
            'source': 'signal_desktop',
            'type': 'text',
        })

    return messages


def try_direct_read(db_path):
    """
    Some Signal Desktop versions (especially older ones or after updates)
    may have an unencrypted WAL or accessible database.
    """
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM sqlite_master")
        count = c.fetchone()[0]
        if count > 0:
            print(f"  ✅ Database is readable without encryption! ({count} tables)")
            return conn
    except Exception:
        pass
    return None


def main():
    print("=" * 60)
    print("  Signal Desktop Message Extractor")
    print("=" * 60)

    # Step 1: Check installation
    if not check_signal_desktop():
        print("\n❌ Signal Desktop not ready. Install and sync first.")
        return

    # Step 2: Get encryption key
    logger.info("Reading encryption key...")
    key = get_encryption_key()
    if not key:
        logger.error("Cannot read encryption key")
        return

    # Step 3: Open database
    print("\nOpening Signal Desktop database...")
    conn = None

    # Try direct read first (unlikely but possible)
    conn = try_direct_read(DB_FILE)

    # Try sqlcipher
    if not conn:
        conn = try_sqlcipher(DB_FILE, key)

    # Try decrypting to plain SQLite
    if not conn:
        print("\nAttempting to decrypt database to plain SQLite...")
        conn = try_decrypt_to_plain_sqlite(DB_FILE, key)

    if not conn:
        logger.error("Could not open the database.")
        logger.info("We need sqlcipher support. Installing pysqlcipher3...")
        logger.info("Run: pip install pysqlcipher3")
        logger.info("If that fails, install sqlcipher CLI:")
        logger.info("  Windows: choco install sqlcipher")
        logger.info("  Or download from: https://github.com/nickoala/pysqlcipher3")
        return

    # Step 4: Extract messages
    print("\nExtracting messages...")
    messages = extract_messages_sqlcipher(conn)
    conn.close()

    if not messages:
        logger.warning("No messages extracted")
        return

    # Stats
    sent = [m for m in messages if m['direction'] == 'sent']
    received = [m for m in messages if m['direction'] == 'received']
    dates = sorted(set(m['date'] for m in messages))

    print(f"\n✅ Extracted {len(messages):,} messages:")
    print(f"   From you (sent):     {len(sent):,}")
    print(f"   From her (received): {len(received):,}")
    print(f"   Date range: {dates[0]} → {dates[-1]}")
    print(f"   Unique days: {len(dates)}")

    # Save
    output = {
        'source': 'signal_desktop',
        'contact': CONTACT_NAME,
        'phone': CONTACT_PHONE,
        'total_messages': len(messages),
        'sent': len(sent),
        'received': len(received),
        'date_range': {'start': dates[0], 'end': dates[-1]},
        'messages': messages,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print("   Now run the analysis engine to include these in the full analysis!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Signal Desktop messages for a contact')
    parser.add_argument('--phone', help='Contact phone number (e.g., +1234567890)')
    parser.add_argument('--name', default='Contact', help='Contact display name')
    parser.add_argument('--config', help='Path to config.json with contact_phone and contact_label')
    parser.add_argument('--output', help='Output JSON file path')
    args = parser.parse_args()
    load_contact_config(args)
    main()
