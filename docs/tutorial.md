# Part 4: Tutorial for Non-Technical Users

Welcome! This guide is for anyone who wants to analyze their own communication data without needing to know how to code.

**Prerequisites**: You will need a computer (Windows/Mac/Linux) and basic familiarity with using the terminal/command prompt.

---

## Step 1: Get Your Data

To analyze your messages, you first need to export them from your phone.

### For Android Users (SMS/MMS)
1.  Download **SMS Backup & Restore** from the Play Store.
2.  Open the app and tap **Backup**.
3.  Select "Text Messages" (and "Call Logs" if desired).
4.  Choose "Local Backup" and save the XML file to your phone.
5.  Transfer this file (`sms_backup.xml`) to your computer.

### For Signal Users
1.  See our [Signal Extraction Guide](docs/signal_extraction.md) (coming soon) or use the `signal_desktop_extractor.py` script if you have Signal Desktop installed.

---

## Step 2: Install the Toolkit

1.  Download and install **Python** from [python.org](https://www.python.org/downloads/). (Make sure to check "Add Python to PATH" during installation).
2.  Download this toolkit as a ZIP file from GitHub (click the green "Code" button -> "Download ZIP") and extract it.
3.  Open your terminal (Command Prompt on Windows, Terminal on Mac).
4.  Navigate to the extracted folder:
    ```bash
    cd Downloads/Communication-Analysis-Toolkit
    ```
5.  Install the required software:
    ```bash
    pip install -r requirements.txt
    ```

---

## Step 3: Set Up Your Case

Think of a "case" as a folder for one specific relationship or investigation.

1.  Create a folder named `my_case` inside the `cases/` folder.
2.  Inside `my_case`, create a folder named `source_data`.
3.  Copy your `sms_backup.xml` file into `cases/my_case/source_data/`.
4.  Create a simple text file named `config.json` inside `cases/my_case/` with this content:
    *(You can use Notepad or TextEdit)*

    ```json
    {
        "case_name": "My Relationship Analysis",
        "user_label": "Me",
        "contact_label": "Them",
        "sms_xml": "./cases/my_case/source_data/sms_backup.xml",
        "output_dir": "./cases/my_case/output",
        "date_start": "2020-01-01",
        "date_end": "2025-12-31"
    }
    ```

---

## Step 4: Run the Analysis

In your terminal, run this command:

```bash
python -m engine.analyzer --config cases/my_case/config.json
```

It will process your messages and tell you when it's done.

---

## Step 5: Read Your Reports

Go to the `cases/my_case/output/` folder. You will find several files:

*   **`TIMELINE.md`**: A story-like view of your relationship day-by-day. Open this in any Markdown viewer or text editor. It highlights arguments, pattern escalations, and mood shifts.
*   **`ANALYSIS.md`**: The numbers. How many messages? Who engaged more? What patterns appeared most often?
*   **`EVIDENCE.md`**: The specific texts. Every time the system flagged a high-conflict pattern (like gaslighting or severe insults), it's listed here with the date and message content.

Questions? Check the [Summary (Part 1)](docs/summary.md) to understand what the patterns mean.
