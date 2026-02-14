import argparse
import sqlite3

parser = argparse.ArgumentParser(description='Explore a Signal export SQLite database')
parser.add_argument('db_path', help='Path to the SQLite database')
parser.add_argument('--output-dir', default='.', help='Output directory')
args = parser.parse_args()

DB_PATH = args.db_path
OUTPUT_DIR = args.output_dir

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check msl_message table structure
print("=== msl_message table structure ===")
cursor.execute("PRAGMA table_info(msl_message)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Get sample data
print("\n=== Sample msl_message data ===")
cursor.execute("SELECT * FROM msl_message LIMIT 5")
rows = cursor.fetchall()
cursor.execute("PRAGMA table_info(msl_message)")
cols = [c[1] for c in cursor.fetchall()]
for row in rows:
    print(dict(zip(cols, row)))

# Check msl_payload table
print("\n=== msl_payload table structure ===")
cursor.execute("PRAGMA table_info(msl_payload)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Get sample payload data
print("\n=== Sample msl_payload data ===")
cursor.execute("SELECT * FROM msl_payload LIMIT 3")
rows = cursor.fetchall()
cursor.execute("PRAGMA table_info(msl_payload)")
cols = [c[1] for c in cursor.fetchall()]
for row in rows:
    print(dict(zip(cols, row)))

# Check thread table
print("\n=== thread table ===")
cursor.execute("PRAGMA table_info(thread)")
cols = [c[1] for c in cursor.fetchall()]
print(f"Columns: {cols}")
cursor.execute("SELECT * FROM thread")
for row in cursor.fetchall():
    print(dict(zip(cols, row)))

# Check recipient table for contact names
print("\n=== Sample recipients ===")
cursor.execute("PRAGMA table_info(recipient)")
recipient_cols = [c[1] for c in cursor.fetchall()]
print(f"Columns: {recipient_cols[:10]}...")
cursor.execute("SELECT _id, system_joined_name, e164, aci FROM recipient WHERE system_joined_name IS NOT NULL LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
