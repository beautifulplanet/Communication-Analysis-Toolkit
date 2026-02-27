# Security Hardening — Project Management Tracker

**Project**: Communication Analysis Toolkit  
**Started**: 2026-02-10  
**Completed**: 2026-02-10  
**Scope**: `9/Communication Analysis Toolkit/` — NO changes outside this folder  
**Status**: ALL PHASES COMPLETE

---

## Phase 1: CRITICAL — Data Exposure & Foundation (Priority: Immediate)

### 1.1 Remove hardcoded PII from `old_unused/` (7 files)
- [ ] `darvo_analyzer.py` — FLUFFY ALPACA, +13478370839, C:\Users\Elite paths
- [ ] `generate_daily_csv.py` — same PII pattern
- [ ] `parse_sms_calls.py` — hardcoded XML/output paths
- [ ] `rebuild_analysis.py` — CONTACT_NAME/PHONE, 7+ paths
- [ ] `unified_timeline_analyzer.py` — FLUFFY ALPACA, +13478370839, all paths
- [ ] `signal_timeline_analyzer.py` — DB_PATH, OUTPUT_DIR
- [ ] `signal_timeline_generator.py` — DB_PATH, OUTPUT_DIR
- [ ] `signal_decrypt.py` — backup_path, output_path at __main__

### 1.2 Remove hardcoded path in active tool
- [ ] `tools/deep_signal_check2.py:113` — `os.walk(r"C:\Users\Elite\Documents\li")`

### 1.3 Add `defusedxml` to `requirements.txt`
- [ ] Add `defusedxml>=0.7.1`

### 1.4 Update `.gitignore`
- [ ] Add `old_unused/` directory
- [ ] Add `*_key.txt` pattern
- [ ] Add `*.backup` pattern (Signal backups)

### 1.5 Pin dependency versions
- [ ] `pycryptodome~=3.19.0` (compatible release)
- [ ] `defusedxml~=0.7.1`
- [ ] Document pysqlcipher3 as optional

---

## Phase 2: HIGH — XML Safety & Memory Bounds

### 2.1 SafeET in `active/generate_monthly_reports.py`
- [ ] Add `defusedxml` import with fallback (already has `import xml.etree.ElementTree as ET`)
- [ ] `~L1110` — `ET.iterparse(SMS_XML)` → use SafeET
- [ ] `~L1126` — `ET.parse(CALLS_XML)` → use SafeET

### 2.2 SafeET in `tools/debug_xml.py`
- [ ] Add defusedxml import with fallback
- [ ] Replace `ET.parse()` with SafeET

### 2.3 JSON size limits
- [ ] `engine/analyzer.py:parse_json_messages()` — check file size before json.load()
- [ ] `active/generate_monthly_reports.py:load_all_data()` — check SIGNAL_DESKTOP_JSON size
- [ ] `active/generate_monthly_reports.py:__main__` — check config.json size

### 2.4 Escape config values in markdown headers
- [ ] `engine/analyzer.py` — escape_md() on config['case_name'], user_label, contact_label in headings
- [ ] `active/generate_monthly_reports.py` — escape_md() on CONTACT_NAME, USER_NAME in headings

---

## Phase 3: MEDIUM — Defense in Depth

### 3.1 SQL identifier safety in exploration tools
- [ ] `tools/explore_db.py` — add _safe_ident() + use it
- [ ] `tools/explore_sms.py` — add _safe_ident() + use it
- [ ] `tools/extract_signal_desktop.py` — add _safe_ident() + use it
- [ ] `tools/read_signal_desktop.py` — add _safe_ident() + use it

### 3.2 Bare `except:` in `old_unused/` (6 files)
- [ ] `darvo_analyzer.py`
- [ ] `generate_daily_csv.py`
- [ ] `parse_sms_calls.py`
- [ ] `unified_timeline_analyzer.py`
- [ ] `signal_timeline_analyzer.py`
- [ ] `signal_timeline_generator.py`

### 3.3 Unbounded `fetchall()` → iterator where possible
- [ ] `active/generate_monthly_reports.py:~L1142` — use `for row in cursor:` instead of fetchall
- [ ] `tools/extract_desktop_messages.py` — use iterator
- [ ] Other exploration tools — add LIMIT or use iterator

### 3.4 Hardcoded path in `tools/deep_signal_check2.py:113`
- [ ] Replace `os.walk(r"C:\Users\Elite\Documents\li")` with argparse parameter

---

## Phase 4: LOW — Polish & Naming

### 4.1 Remove key leaks in old_unused
- [ ] `signal_decrypt_v2.py:~L223` — remove/mask cipher_key.hex() print  
- [ ] `signal_decrypt_v3.py:~L195` — remove/mask cipher_key.hex() print  

### 4.2 Fix old project name references
- [ ] `engine/analyzer.py:~L467` — "Communication Analysis" banner text
- [ ] `engine/analyzer.py:main()` — "COMMUNICATION ANALYSIS TOOLKIT" banner text

### 4.3 XML & escape in old_unused (archived but should be clean)
- [ ] Add defusedxml + escape_md() patterns to old_unused files
  (OR just ensure .gitignore blocks these — lower priority since archived)

---

## Completion Criteria

- [x] `grep -r "Elite\|FLUFFY\|13478370839\|Liming" .` returns 0 hits in active/engine/tools AND old_unused
- [x] No bare `except:` — only `except Exception:` or more specific
- [x] All XML parsing uses SafeET where available
- [x] All user content in markdown escaped via escape_md()
- [x] defusedxml in requirements.txt (pinned ~=0.7.1)
- [x] pycryptodome pinned (~=3.19.0)
- [x] .gitignore covers old_unused/, *_key.txt, *.backup
- [x] No encryption keys printed to stdout
- [x] All SQL identifiers validated via _safe_ident()
- [x] JSON file size limits before json.load()
- [x] Config values escaped in markdown report headers
- [x] Old project name updated to "Communication Analysis Toolkit"
- [x] All files pass `py_compile` syntax check

---

*All phases completed 2026-02-10. Final verification: zero PII, zero bare excepts, zero raw XML parsing, zero unescaped user content in markdown.*
