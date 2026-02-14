"""
Parse manual_signal_messages.txt into a JSON file compatible with the analysis engine.
Supports flexible timestamp formats and direction keywords.

Usage:
  python parse_manual_messages.py --input messages.txt --output messages.json
  python parse_manual_messages.py --config cases/my_project/config.json
"""
import argparse
import json
import os
import re
from datetime import datetime

INPUT_FILE = ""
OUTPUT_FILE = ""

# Direction aliases — configurable per case
RECEIVED_KEYWORDS = {'her', 'received', 'from her', 'she', 'them', 'from them'}
SENT_KEYWORDS = {'me', 'sent', 'from me', 'i', 'my', 'mine'}

# Flexible timestamp patterns
TIMESTAMP_PATTERNS = [
    # [2026-01-15 14:30:00]
    (r'\[(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2}(?::\d{2})?)\]', '%Y-%m-%d', None),
    # [2026-01-15]
    (r'\[(\d{4}-\d{2}-\d{2})\]', '%Y-%m-%d', None),
    # [01/15/2026 2:30 PM]
    (r'\[(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\]', '%m/%d/%Y', '%I:%M %p'),
    # [01/15/2026]
    (r'\[(\d{1,2}/\d{1,2}/\d{4})\]', '%m/%d/%Y', None),
    # [Jan 15, 2026 2:30 PM]
    (r'\[([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\]', '%b %d, %Y', '%I:%M %p'),
    # [Jan 15, 2026]
    (r'\[([A-Za-z]+\s+\d{1,2},?\s+\d{4})\]', '%b %d, %Y', None),
]


def parse_timestamp(ts_text):
    """Try to parse a timestamp string into a datetime object."""
    for pattern, date_fmt, time_fmt in TIMESTAMP_PATTERNS:
        m = re.match(pattern, ts_text)
        if m:
            groups = m.groups()
            try:
                if len(groups) == 2 and groups[1]:
                    # Has date and time
                    date_str = groups[0]
                    time_str = groups[1].strip()
                    dt = datetime.strptime(date_str, date_fmt)
                    # Try to parse time
                    if time_fmt:
                        t = datetime.strptime(time_str, time_fmt)
                    elif ':' in time_str:
                        parts = time_str.split(':')
                        hour = int(parts[0])
                        minute = int(parts[1]) if len(parts) > 1 else 0
                        second = int(parts[2]) if len(parts) > 2 else 0
                        t = dt.replace(hour=hour, minute=minute, second=second)
                        return t
                    else:
                        return dt
                    return dt.replace(hour=t.hour, minute=t.minute, second=t.second)
                if len(groups) == 1:
                    # Date only
                    dt = datetime.strptime(groups[0].replace(',', ''), date_fmt)
                    return dt
            except ValueError:
                continue
    return None


def parse_direction(dir_text):
    """Determine if this is a 'sent' or 'received' message."""
    dir_lower = dir_text.strip().lower()
    if dir_lower in RECEIVED_KEYWORDS:
        return 'received'
    if dir_lower in SENT_KEYWORDS:
        return 'sent'
    return None


def parse_manual_messages(input_path):
    """Parse the manual message file."""
    messages = []
    errors = []

    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        return messages, errors

    with open(input_path, encoding='utf-8') as f:
        lines = f.readlines()

    line_num = 0
    for line in lines:
        line_num += 1
        line = line.rstrip('\n\r')

        # Skip comments and blanks
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Try to match: [timestamp] direction: message
        # More flexible: look for [...] then direction: then message
        bracket_match = re.match(r'(\[.+?\])\s*(.+?):\s*(.*)', line)
        if not bracket_match:
            # Try without brackets: just date direction: message
            no_bracket = re.match(r'(\d{4}-\d{2}-\d{2})\s+(.+?):\s*(.*)', line)
            if no_bracket:
                date_str, dir_text, body = no_bracket.groups()
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Line {line_num}: Could not parse date: {line[:80]}")
                    continue
                direction = parse_direction(dir_text)
                if not direction:
                    errors.append(f"Line {line_num}: Unknown direction '{dir_text}' (use her/me/sent/received)")
                    continue
                messages.append({
                    'timestamp': int(dt.timestamp() * 1000),
                    'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'direction': direction,
                    'body': body.replace('\\n', '\n'),
                    'source': 'signal_manual',
                    'type': 'text',
                    'line_num': line_num,
                })
                continue
            errors.append(f"Line {line_num}: Could not parse format: {line[:80]}")
            continue

        ts_text, dir_text, body = bracket_match.groups()
        dt = parse_timestamp(ts_text)
        if not dt:
            errors.append(f"Line {line_num}: Could not parse timestamp: {ts_text}")
            continue

        direction = parse_direction(dir_text)
        if not direction:
            errors.append(f"Line {line_num}: Unknown direction '{dir_text}' (use her/me/sent/received)")
            continue

        messages.append({
            'timestamp': int(dt.timestamp() * 1000),
            'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M:%S'),
            'direction': direction,
            'body': body.replace('\\n', '\n'),
            'source': 'signal_manual',
            'type': 'text',
            'line_num': line_num,
        })

    # Sort by timestamp
    messages.sort(key=lambda m: m['timestamp'])
    return messages, errors


def main():
    print("=" * 60)
    print("  Parsing Manual Signal Messages")
    print("=" * 60)

    messages, errors = parse_manual_messages(INPUT_FILE)

    if errors:
        print(f"\n⚠️  {len(errors)} parsing errors:")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")

    sent = [m for m in messages if m['direction'] == 'sent']
    received = [m for m in messages if m['direction'] == 'received']

    print(f"\n✅ Parsed {len(messages)} messages:")
    print(f"   From her (received): {len(received)}")
    print(f"   From you (sent):     {len(sent)}")

    if messages:
        dates = sorted(set(m['date'] for m in messages))
        print(f"   Date range: {dates[0]} → {dates[-1]}")
        print(f"   Unique days: {len(dates)}")

    # Save
    output = {
        'source': 'manual_input',
        'parsed_from': INPUT_FILE,
        'total_messages': len(messages),
        'sent': len(sent),
        'received': len(received),
        'messages': messages,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print("   Run the analysis engine to include these in the analysis.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse manual message text file into JSON')
    parser.add_argument('--input', help='Path to manual_signal_messages.txt')
    parser.add_argument('--output', help='Path to output JSON file')
    parser.add_argument('--config', help='Path to config.json (uses manual_signal_json field)')
    cli_args = parser.parse_args()

    if cli_args.config:
        with open(cli_args.config, encoding='utf-8') as _f:
            _cfg = json.load(_f)
        INPUT_FILE = cli_args.input or _cfg.get("manual_signal_txt", "")
        OUTPUT_FILE = _cfg.get("manual_signal_json", "")
    else:
        INPUT_FILE = cli_args.input or ""
        OUTPUT_FILE = cli_args.output or ""

    if not INPUT_FILE or not OUTPUT_FILE:
        print("Error: --input and --output are required (or use --config)")
        exit(1)

    main()
