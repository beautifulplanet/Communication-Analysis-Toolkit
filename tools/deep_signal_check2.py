"""Deep investigation part 2 — fix column names and check remaining items."""
import sqlite3
import os
import re
import argparse

parser = argparse.ArgumentParser(description='Deep Signal database investigation part 2')
parser.add_argument('db_path', help='Path to the SQLite database')
parser.add_argument('--export-dir', default='.', help='Signal export directory')
args = parser.parse_args()

DB = args.db_path
EXPORT_DIR = args.export_dir
def _safe_ident(name: str) -> str:
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


conn = sqlite3.connect(DB)
c = conn.cursor()

# 9. Check disappearing message settings
print("9. DISAPPEARING MESSAGE SETTINGS:")
c.execute("PRAGMA table_info(recipient)")
rcols = [col[1] for col in c.fetchall()]
exp_cols = [col for col in rcols if 'expir' in col.lower() or 'timer' in col.lower()]
print(f"   Expiration-related columns: {exp_cols}")
for col in exp_cols:
    col = _safe_ident(col)
    c.execute(f"SELECT _id, {col} FROM recipient WHERE {col} > 0 LIMIT 20")
    rows = c.fetchall()
    if rows:
        print(f"   {col}:")
        for r in rows:
            val = r[1]
            if isinstance(val, int) and val > 0:
                if val < 60: s = f"{val}s"
                elif val < 3600: s = f"{val//60}m"
                elif val < 86400: s = f"{val//3600}h"
                else: s = f"{val//86400}d"
                print(f"     recipient {r[0]}: {s} ({val}s)")

# 10. Thread table
print("\n10. THREAD TABLE:")
c.execute("PRAGMA table_info(thread)")
tcols = [col[1] for col in c.fetchall()]
print(f"   Columns: {tcols}")
c.execute("SELECT * FROM thread")
for row in c.fetchall():
    d = dict(zip(tcols, row))
    print(f"   thread {d['_id']}: recipient={d.get('recipient_id','?')} meaningful={d.get('meaningful_messages','?')} snippet='{str(d.get('snippet',''))[:60]}'")

# 11. Check signalbackup-tools logs
print("\n11. SIGNALBACKUP-TOOLS LOGS:")
parent_dir = os.path.dirname(EXPORT_DIR)
for fname in ['sbt_stdout.txt', 'sbt_stderr.txt']:
    fpath = os.path.join(parent_dir, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        print(f"\n   === {fname} ({size:,} bytes, {len(content)} chars) ===")
        if len(content) > 4000:
            print(content[:2000])
            print("\n   ... (middle truncated) ...\n")
            print(content[-2000:])
        else:
            print(content if content.strip() else "   (empty)")
    else:
        print(f"   {fname}: NOT FOUND")

# 12. CRITICAL: The sqlite_sequence for message is MISSING
# This means either:
# a) The message table was TRUNCATED (DELETE + VACUUM), or
# b) The table never had auto-increment, or
# c) The table was recreated empty
print("\n12. CRITICAL ANALYSIS:")
print("   message table has 0 rows AND no sqlite_sequence entry")
print("   BUT msl_message references message_ids 195132-201829")
print("   AND attachment references message_ids 9-201828")
print("   AND reaction references message_ids 2395-195460")
print()
print("   This means ~201,829 messages EXISTED at some point!")
print("   They were deleted — either by:")
print("   a) Disappearing messages timer")
print("   b) Manual deletion")
print("   c) Signal's auto-cleanup")

# 13. Check if the backup file itself exists
print("\n13. LOOKING FOR .backup FILES:")
scan_dir = os.path.dirname(EXPORT_DIR) if EXPORT_DIR != '.' else '.'
for root, dirs, files in os.walk(scan_dir):
    # Skip deep nested dirs
    depth = root.replace(scan_dir, "").count(os.sep)
    if depth > 2:
        continue
    for f in files:
        lower = f.lower()
        if '.backup' in lower or lower.endswith('.bin') or 'signal' in lower and lower.endswith('.bak'):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            print(f"   {fpath} ({size:,} bytes)")

# 14. Check sbt_help for the decryption command used
print("\n14. SBT_HELP.TXT:")
fpath = os.path.join(parent_dir, "sbt_help.txt")
if os.path.exists(fpath):
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    # Find relevant lines about export/output options
    for line in content.split('\n'):
        if any(w in line.lower() for w in ['output', 'export', 'message', 'sqlite', 'database', 'decrypt']):
            print(f"   {line.rstrip()}")
else:
    print("   NOT FOUND")

# 15. Check what the attachment data_file paths look like
print("\n15. ATTACHMENT FILE PATHS (sample):")
c.execute("SELECT data_file, content_type FROM attachment WHERE data_file IS NOT NULL LIMIT 5")
for r in c.fetchall():
    print(f"   {r[0]} ({r[1]})")

# 16. Check if there's any data in the attachment unique_id or similar that maps to files on disk
print("\n16. SIGNAL EXPORT SUBDIRECTORIES:")
for item in sorted(os.listdir(EXPORT_DIR)):
    fpath = os.path.join(EXPORT_DIR, item)
    if os.path.isdir(fpath):
        count = sum(1 for _ in os.scandir(fpath))
        print(f"   {item}/ ({count} items)")

conn.close()
