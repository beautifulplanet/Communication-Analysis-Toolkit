import logging
import sqlite3
from collections.abc import Generator
from typing import Optional
from contextlib import contextmanager
from pathlib import Path

log = logging.getLogger(__name__)

# Constants
DB_FILENAME = "cases.db"
SCHEMA_FILENAME = "schema.sql"

def get_base_dir() -> Path:
    """Return the base directory of the project."""
    # current file is in engine/db.py -> parent is engine/ -> parent is root
    return Path(__file__).parent.parent

def get_cases_dir() -> Path:
    """Return the directory where case data is stored."""
    return get_base_dir() / "cases"

def get_db_path() -> Path:
    """Return the absolute path to the main database file."""
    db_dir = get_cases_dir()
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / DB_FILENAME

def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initialize the database with the schema.
    Idempotent: can be run multiple times safely (IF NOT EXISTS).
    """
    target_path = db_path or get_db_path()
    schema_path = Path(__file__).parent / SCHEMA_FILENAME

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    log.info(f"Initializing database at {target_path}")

    try:
        with sqlite3.connect(target_path) as conn:
            # Optimize for performance
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            # Apply schema
            with open(schema_path, encoding="utf-8") as f:
                schema_sql = f.read()
                conn.executescript(schema_sql)

        log.info("Database initialized successfully.")
    except sqlite3.Error as e:
        log.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def get_db_connection(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures connections are closed and rows are returned as dict-like objects.
    """
    target_path = db_path or get_db_path()

    # Auto-initialize if missing
    if not target_path.exists():
        init_db(target_path)

    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    # Enforce foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
