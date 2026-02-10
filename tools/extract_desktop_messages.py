"""
Extract all Signal Desktop messages for a target contact.
Exports both sent AND received messages with timestamps.

Usage: python extract_desktop_messages.py --key-file KEY_FILE --db-path DB_PATH --phone PHONE --output-dir DIR
"""
import json
import os
import sys
import re
import argparse
from datetime import datetime, timezone


def _validate_hex_key(key: str) -> str:
    if not key or not re.match(r'^[0-9a-fA-F]+$', key):
        raise ValueError("Invalid encryption key format")
    return key


def main():
    parser = argparse.ArgumentParser(description='Extract Signal Desktop messages for a contact')
    parser.add_argument('--key-file', required=True, help='Path to file containing the hex decryption key')
    parser.add_argument('--db-path', required=True, help='Path to the Signal Desktop SQLCipher database')
    parser.add_argument('--phone', required=True, help='Target contact phone number (e.g., +1234567890)')
    parser.add_argument('--name', default='Contact', help='Contact display name')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    args = parser.parse_args()

    with open(args.key_file) as f:
        db_key = _validate_hex_key(f.read().strip())

    import sqlcipher3
    conn = sqlcipher3.connect(args.db_path)
    conn.row_factory = sqlcipher3.Row
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA key=\"x'{db_key}'\"")
    cursor.execute("PRAGMA cipher_compatibility = 4")

    TARGET_PHONE = args.phone
    CONTACT_NAME = args.name

    print("=== Finding target conversation ===")
    cursor.execute("SELECT * FROM conversations LIMIT 1")
    row = cursor.fetchone()
    cols = row.keys() if row else []
    print(f"Conversation columns: {cols}")

    # Find by phone number
    phone_digits = TARGET_PHONE.replace("+", "")
    cursor.execute("""
        SELECT id, type, json
        FROM conversations
        WHERE json LIKE ?
    """, (f'%{phone_digits}%',))
    matches = cursor.fetchall()
    print(f"\nFound {len(matches)} matching conversation(s)")

    conversation_ids = []
    for m in matches:
        data = json.loads(m['json'])
        cid = m['id']
        ctype = m['type']
        name = data.get('name', data.get('profileName', data.get('e164', 'unknown')))
        print(f"  ID: {cid}, Type: {ctype}, Name: {name}")
        conversation_ids.append(cid)

    if not conversation_ids:
        print("No matching conversation found!")
        conn.close()
        sys.exit(1)

    # Step 2: Get message columns
    print("\n=== Message schema ===")
    cursor.execute("PRAGMA table_info(messages)")
    msg_cols = [(r['name'], r['type']) for r in cursor.fetchall()]
    print(f"Columns: {[c[0] for c in msg_cols]}")

    # Step 3: Extract messages for target conversation
    print("\n=== Extracting messages ===")
    conv_id = conversation_ids[0]

    cursor.execute("""
        SELECT id, json, type, body, sent_at, received_at,
               conversationId, source, sourceServiceId, hasAttachments
        FROM messages
        WHERE conversationId = ?
        ORDER BY sent_at ASC
    """, (conv_id,))

    messages = []
    count = 0
    for row in cursor:
        count += 1
        data = json.loads(row['json']) if row['json'] else {}

        sent_at = row['sent_at'] or data.get('sent_at', 0)
        body = row['body'] or data.get('body', '')
        msg_type = row['type'] or data.get('type', '')

        if msg_type in ('outgoing',):
            direction = 'sent'
        elif msg_type in ('incoming',):
            direction = 'received'
        else:
            direction = msg_type or 'unknown'

        if sent_at and sent_at > 1000000000000:
            dt = datetime.fromtimestamp(sent_at / 1000, tz=timezone.utc)
        elif sent_at:
            dt = datetime.fromtimestamp(sent_at, tz=timezone.utc)
        else:
            dt = None

        ts_str = dt.strftime('%Y-%m-%d %H:%M:%S') if dt else 'unknown'

        msg = {
            'id': row['id'],
            'timestamp': ts_str,
            'timestamp_ms': sent_at,
            'direction': direction,
            'type': msg_type,
            'body': body,
            'has_attachments': bool(row['hasAttachments']),
        }

        if data.get('editHistory'):
            msg['edited'] = True
            msg['edit_history'] = [
                {'body': e.get('body', ''), 'timestamp': e.get('timestamp', 0)}
                for e in data['editHistory']
            ]

        if data.get('reactions'):
            msg['reactions'] = data['reactions']

        if data.get('quote'):
            q = data['quote']
            msg['reply_to'] = q.get('text', '')[:200]

        messages.append(msg)

    print(f"Total messages in conversation: {count:,}")

    sent = sum(1 for m in messages if m['direction'] == 'sent')
    received = sum(1 for m in messages if m['direction'] == 'received')
    with_text = sum(1 for m in messages if m['body'])
    types = {}
    for m in messages:
        t = m['type']
        types[t] = types.get(t, 0) + 1

    print(f"  Sent by you: {sent:,}")
    print(f"  Received: {received:,}")
    print(f"  With text: {with_text:,}")
    print(f"  Types: {types}")

    if messages:
        print(f"  Date range: {messages[0]['timestamp']} to {messages[-1]['timestamp']}")

    # Save to JSON
    os.makedirs(args.output_dir, exist_ok=True)
    out_file = os.path.join(args.output_dir, "signal_desktop_messages.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            'contact': CONTACT_NAME,
            'phone': TARGET_PHONE,
            'conversation_id': conv_id,
            'total_messages': len(messages),
            'sent': sent,
            'received': received,
            'date_range': {
                'start': messages[0]['timestamp'] if messages else None,
                'end': messages[-1]['timestamp'] if messages else None,
            },
            'messages': messages
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {out_file} ({os.path.getsize(out_file) / 1024 / 1024:.1f} MB)")

    # Show sample
    print("\n=== Sample messages (first 10 with text) ===")
    text_msgs = [m for m in messages if m['body']]
    for m in text_msgs[:10]:
        arrow = "\u2192" if m['direction'] == 'sent' else "\u2190"
        print(f"  {m['timestamp']} {arrow} {m['body'][:100]}")

    conn.close()
    print("\nDone!")


if __name__ == '__main__':
    main()
