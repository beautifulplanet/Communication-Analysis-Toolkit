import argparse
import re
import sqlite3


def _safe_ident(name: str) -> str:
    """Validate SQL identifier to prevent injection."""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name

parser = argparse.ArgumentParser(description='Explore a Signal export SQLite database')
parser.add_argument('db_path', help='Path to the SQLite database')
parser.add_argument('--output', default='db_exploration.txt', help='Output file path')
args = parser.parse_args()

DB_PATH = args.db_path
OUTPUT = args.output

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

with open(OUTPUT, "w", encoding="utf-8") as f:
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]

    f.write("=== ALL TABLES ===\n")
    for t in sorted(tables):
        try:
            safe_t = _safe_ident(t)
            cursor.execute(f"SELECT COUNT(*) FROM [{safe_t}]")
            count = cursor.fetchone()[0]
            if count > 0:
                f.write(f"  {t}: {count:,} rows\n")
        except ValueError:
            f.write(f"  {t}: skipped (invalid name)\n")

    # Check message table
    f.write("\n=== MESSAGE TABLE SCHEMA ===\n")
    cursor.execute("PRAGMA table_info(message)")
    for c in cursor.fetchall():
        f.write(f"  {c[1]} ({c[2]})\n")

    # Check if message table has any rows
    cursor.execute("SELECT COUNT(*) FROM message")
    msg_count = cursor.fetchone()[0]
    f.write(f"\nMessage table row count: {msg_count}\n")

    # Thread details with message counts
    f.write("\n=== THREAD DETAILS ===\n")
    cursor.execute("SELECT * FROM thread")
    thread_cols = [d[0] for d in cursor.description]
    f.write(f"Columns: {thread_cols}\n\n")
    cursor.execute("SELECT * FROM thread")
    for row in cursor.fetchall():
        f.write(f"{dict(zip(thread_cols, row))}\n")

    # Check msl_payload dates - see if we can identify SMS vs Signal
    f.write("\n=== MSL_PAYLOAD SAMPLE ===\n")
    cursor.execute("PRAGMA table_info(msl_payload)")
    payload_cols = [c[1] for c in cursor.fetchall()]
    f.write(f"Columns: {payload_cols}\n\n")

    cursor.execute("SELECT * FROM msl_payload LIMIT 10")
    for row in cursor.fetchall():
        f.write(f"{dict(zip(payload_cols, row))}\n")

    # Check for different message types in the data
    f.write("\n=== CHECKING FOR SMS INDICATORS ===\n")

    # Check recipient for sms_related fields
    cursor.execute("SELECT _id, system_joined_name, e164, registered FROM recipient WHERE e164 IS NOT NULL LIMIT 20")
    f.write("Recipients with phone numbers:\n")
    for row in cursor.fetchall():
        f.write(f"  ID={row[0]}, Name='{row[1]}', Phone={row[2]}, Registered={row[3]}\n")

conn.close()
print(f"Saved to {OUTPUT}")
