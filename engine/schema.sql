-- ============================================================================
-- Communication Forensic Tool - SQLite Schema (v1)
-- Designed for: Performance (100k+ msgs), Privacy (Local-first), Integrity
-- ============================================================================

-- Enable strict foreign key enforcement
PRAGMA foreign_keys = ON;

-- 1. CASES: Metadata registry for imported datasets
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                  -- Display name (e.g. "Export 2025")
    case_uuid TEXT UNIQUE NOT NULL,      -- UUID for folder matching
    user_name TEXT,                      -- Identified device owner
    contact_name TEXT,                   -- Identified other party
    source_path TEXT,                    -- Original import location
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 2. MESSAGES: Immutable raw evidence
--    Partitioning strategy: Indexed by date for timeline views
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    
    -- Temporal Data
    timestamp INTEGER NOT NULL,          -- Unix timestamp (UTC) for sorting
    date TEXT NOT NULL,                  -- YYYY-MM-DD for partitioning
    time TEXT NOT NULL,                  -- HH:MM for display
    
    -- Content
    source TEXT NOT NULL,                -- 'sms', 'whatsapp', 'signal'
    direction TEXT NOT NULL,             -- 'user->contact', 'contact->user'
    body TEXT,                           -- Content (nullable for media-only)
    media_type TEXT DEFAULT 'text',      -- 'text', 'image', 'audio', 'call'
    duration INTEGER DEFAULT 0,          -- For calls (seconds)
    
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- 2b. CALLS: Phone and Signal call logs
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    
    timestamp INTEGER NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    
    source TEXT NOT NULL,                -- 'phone', 'signal'
    direction TEXT NOT NULL,             -- 'incoming', 'outgoing', 'missed'
    duration INTEGER DEFAULT 0,
    call_type TEXT DEFAULT 'audio_call', -- 'audio_call', 'video_call'
    
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_case_date ON messages(case_id, date);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- 3. ANALYSIS: Derived intelligence (Mutable/Re-computable)
--    Separated from messages to allow re-running analysis without touching evidence
CREATE TABLE IF NOT EXISTS message_analysis (
    message_id INTEGER PRIMARY KEY,
    
    -- Heuristics
    is_hurtful BOOLEAN DEFAULT 0,
    severity TEXT,                       -- 'mild', 'moderate', 'severe'
    is_apology BOOLEAN DEFAULT 0,
    sentiment_score REAL DEFAULT 0.0,    
    
    -- JSON blobs for complex structures (Lists of strings)
    patterns_json TEXT DEFAULT '[]',     -- e.g. ["gaslighting", "darvo"]
    keywords_json TEXT DEFAULT '[]',     -- e.g. ["idiot", "always"]
    supportive_json TEXT DEFAULT '[]',   -- e.g. ["validation", "empathy"]
    
    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
);

-- 4. SUMMARIES: Pre-computed daily stats for fast dashboard loading
CREATE TABLE IF NOT EXISTS daily_summaries (
    case_id INTEGER NOT NULL,
    date TEXT NOT NULL,                  -- YYYY-MM-DD
    
    msg_count INTEGER DEFAULT 0,
    avg_sentiment REAL DEFAULT 0.0,
    hurtful_count INTEGER DEFAULT 0,
    patterns_count INTEGER DEFAULT 0,
    
    PRIMARY KEY (case_id, date),
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);
