# Forensic Cases Directory

**⚠️ PRIVACY WARNING ⚠️**

This directory contains **sensitive personal data** (SMS backups, chat logs, analysis reports).

## Privacy Rules
1.  **Git Ignored:** This folder is excluded from version control (via `.gitignore`).
2.  **Local Only:** Do not sync this folder to DropBox, Google Drive, or shared servers unless encrypted.
3.  **Structure:**
    ```
    cases/
    ├── sample/           # Included example data (safe to commit)
    └── [case_name]/      # YOUR PRIVATE DATA
        ├── source_data/  # Raw exports (XML, CSV)
        ├── config.json   # Analysis settings
        └── output/       # Generated reports (markdown, json)
    ```
