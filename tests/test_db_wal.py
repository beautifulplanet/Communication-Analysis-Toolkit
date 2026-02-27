import contextlib
import os
import sys

sys.path.append(os.getcwd())

with contextlib.suppress(ImportError):
    from engine.db import get_db_connection, init_db

def test_db_settings():
    print("Testing DB Settings...")
    # Ensure init
    init_db()

    with get_db_connection() as conn:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        print(f"Journal Mode: {mode}")

        sync = conn.execute("PRAGMA synchronous;").fetchone()[0]
        print(f"Synchronous: {sync}")

        timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        print(f"Busy Timeout: {timeout}")

        if mode.lower() != "wal":
            print("FAIL: Journal mode is not WAL")
        elif sync != 1:
            print("FAIL: Synchronous is not NORMAL (1)")
        elif timeout != 5000:
            print("FAIL: Busy timeout is not 5000")
        else:
            print("SUCCESS: All DB settings correct.")

if __name__ == "__main__":
    test_db_settings()
