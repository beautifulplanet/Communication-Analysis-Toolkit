"""
Deep investigation: Is the Signal backup supposed to have all messages?
Check everything - message table schema, all possible message storage,
the decryption tool output, and whether messages were deleted vs never extracted.
"""
import argparse
import os
import sqlite3

parser = argparse.ArgumentParser(description='Deep investigation of Signal backup database')
parser.add_argument('db_path', help='Path to the SQLite database')
parser.add_argument('--export-dir', default='.', help='Signal export directory to scan for files')
args = parser.parse_args()

DB = args.db_path
EXPORT_DIR = args.export_dir

conn = sqlite3.connect(DB)
c = conn.cursor()

print("=" * 70)
print("  DEEP SIGNAL DATABASE INVESTIGATION")
print("=" * 70)

# 1. Message table — does it EXIST and what's its schema?
print("\n1. MESSAGE TABLE SCHEMA:")
c.execute("PRAGMA table_info(message)")
cols = c.fetchall()
for col in cols:
    print(f"   {col[1]:30s} {col[2]:15s} {'NOT NULL' if col[3] else ''}")

c.execute("SELECT COUNT(*) FROM message")
print(f"\n   Row count: {c.fetchone()[0]}")

# 2. Check if message table has an auto-increment counter showing rows WERE there
c.execute("SELECT * FROM sqlite_sequence WHERE name='message'")
seq = c.fetchone()
if seq:
    print(f"   sqlite_sequence: {seq} (messages WERE here, max _id was {seq[1]})")
else:
    print("   No sqlite_sequence entry for message table")

# 3. Check ALL sqlite_sequence to see what tables had data
print("\n2. ALL TABLE AUTO-INCREMENT SEQUENCES (shows historical max IDs):")
c.execute("SELECT * FROM sqlite_sequence ORDER BY seq DESC")
for row in c.fetchall():
    print(f"   {row[0]:40s} max_id: {row[1]}")

# 4. Check msl_message — does it reference message IDs?
print("\n3. MSL_MESSAGE → MESSAGE ID REFERENCES:")
c.execute("SELECT MIN(message_id), MAX(message_id), COUNT(*) FROM msl_message")
row = c.fetchone()
print(f"   message_id range: {row[0]} → {row[1]} ({row[2]} rows)")

# 5. Check attachment — does it reference message IDs?
print("\n4. ATTACHMENT → MESSAGE ID REFERENCES:")
c.execute("SELECT MIN(message_id), MAX(message_id), COUNT(*) FROM attachment")
row = c.fetchone()
print(f"   message_id range: {row[0]} → {row[1]} ({row[2]} rows)")

# 6. Check reaction — does it reference message IDs?
print("\n5. REACTION → MESSAGE ID REFERENCES:")
c.execute("SELECT MIN(message_id), MAX(message_id), COUNT(*) FROM reaction")
row = c.fetchone()
print(f"   message_id range: {row[0]} → {row[1]} ({row[2]} rows)")

# 7. Check if there's a separate messages database file
print("\n6. ALL .sqlite AND .db FILES IN EXPORT DIR:")
for root, dirs, files in os.walk(EXPORT_DIR):
    for f in files:
        if f.endswith(('.sqlite', '.db', '.sqlite3', '.sql')):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            print(f"   {fpath} ({size:,} bytes)")

# 8. Total database file size
db_size = os.path.getsize(DB)
print(f"\n7. DATABASE SIZE: {db_size:,} bytes ({db_size/1024/1024:.1f} MB)")

# 9. Check signalbackup-tools output/logs for clues
print("\n8. SIGNAL EXPORT FOLDER CONTENTS:")
for item in sorted(os.listdir(EXPORT_DIR)):
    fpath = os.path.join(EXPORT_DIR, item)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        print(f"   {item:40s} {size:>12,} bytes")
    else:
        # Count files in subdirectory
        try:
            count = sum(1 for _ in os.scandir(fpath))
            print(f"   {item + '/':40s} ({count} items)")
        except Exception:
            print(f"   {item + '/':40s}")

# 10. Check if disappearing messages setting is in the database
print("\n9. DISAPPEARING MESSAGE SETTINGS:")
c.execute("SELECT _id, recipient_id, message_expiration_time FROM recipient WHERE message_expiration_time > 0")
rows = c.fetchall()
for r in rows:
    exp_seconds = r[2]
    if exp_seconds < 60:
        exp_str = f"{exp_seconds}s"
    elif exp_seconds < 3600:
        exp_str = f"{exp_seconds//60}m"
    elif exp_seconds < 86400:
        exp_str = f"{exp_seconds//3600}h"
    else:
        exp_str = f"{exp_seconds//86400}d"
    print(f"   recipient {r[0]}: expiration = {exp_str} ({exp_seconds}s)")

# 11. Check thread table for message counts
print("\n10. THREAD TABLE — meaningful_messages counts:")
c.execute("SELECT _id, recipient_id, meaningful_messages, snippet, date FROM thread")
for r in c.fetchall():
    print(f"   thread {r[0]}: recipient={r[1]} meaningful_msgs={r[2]} snippet='{r[3][:50] if r[3] else 'NULL'}' last_date={r[4]}")

# 12. Check if signalbackup-tools was used with --no-messages or similar
print("\n11. CHECKING FOR SIGNALBACKUP-TOOLS OUTPUT FILES:")
sbt_files = ['sbt_stdout.txt', 'sbt_stderr.txt']
parent_dir = os.path.dirname(EXPORT_DIR)
for f in sbt_files:
    fpath = os.path.join(parent_dir, f)
    if os.path.exists(fpath):
        with open(fpath, encoding='utf-8', errors='replace') as fh:
            content = fh.read()
        print(f"\n   === {f} ({len(content)} chars) ===")
        # Show first 2000 chars and last 1000
        if len(content) > 3000:
            print(content[:2000])
            print("   ... (truncated) ...")
            print(content[-1000:])
        else:
            print(content)

# 13. Is there a raw .backup file we haven't fully extracted?
print("\n12. LOOKING FOR SIGNAL BACKUP FILES (.backup):")
for root, dirs, files in os.walk(parent_dir):
    for f in files:
        if '.backup' in f.lower() or f.endswith('.bin'):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            print(f"   {fpath} ({size:,} bytes)")

conn.close()
