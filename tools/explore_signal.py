"""
Signal database explorer - fixed version
"""
import argparse
import sqlite3
from datetime import datetime

parser = argparse.ArgumentParser(description='Explore Signal export database tables')
parser.add_argument('db_path', help='Path to the SQLite database')
args = parser.parse_args()

DB_PATH = args.db_path

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get msl_payload schema
print("msl_payload columns:")
cursor.execute("PRAGMA table_info(msl_payload)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# Get msl_message schema
print("\nmsl_message columns:")
cursor.execute("PRAGMA table_info(msl_message)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# Get msl_recipient schema
print("\nmsl_recipient columns:")
cursor.execute("PRAGMA table_info(msl_recipient)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

# Sample data from msl_payload
print("\nSample msl_payload (first 5):")
cursor.execute("SELECT * FROM msl_payload ORDER BY date_sent DESC LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row}")

# Check date range
print("\nDate range in msl_payload:")
cursor.execute("SELECT MIN(date_sent), MAX(date_sent) FROM msl_payload")
min_date, max_date = cursor.fetchone()
if min_date:
    print(f"  Min: {datetime.fromtimestamp(min_date/1000)}")
    print(f"  Max: {datetime.fromtimestamp(max_date/1000)}")

# Get recipient table columns
print("\nrecipient columns:")
cursor.execute("PRAGMA table_info(recipient)")
for col in cursor.fetchall()[:15]:
    print(f"  {col[1]} ({col[2]})")

conn.close()
