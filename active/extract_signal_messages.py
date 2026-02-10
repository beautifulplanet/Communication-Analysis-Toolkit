"""
Signal MSL Payload Extractor
Extracts readable message text from Signal's msl_payload protobuf blobs.
MSL = Message Send Log = YOUR outgoing messages only.
"""
import sqlite3
import json
import argparse
from datetime import datetime


def decode_varint(data, pos):
    """Decode a protobuf varint starting at pos. Returns (value, new_pos)."""
    value = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80):
            break
    return value, pos


def extract_text_from_protobuf(blob):
    """
    Extract text fields from a Signal Content protobuf blob.
    Signal's Content message has field 1 = DataMessage, which has field 1 = body (string).
    Returns the message body text or None.
    """
    i = 0
    while i < len(blob):
        if i >= len(blob):
            break
        tag = blob[i]
        field_num = tag >> 3
        wire_type = tag & 0x07
        i += 1

        if wire_type == 2:  # Length-delimited (string, bytes, or embedded message)
            length, i = decode_varint(blob, i)
            if length < 0 or i + length > len(blob):
                break
            field_data = blob[i:i + length]
            i += length

            if field_num == 1:
                # Field 1 at top level = DataMessage (embedded) or body string
                # Try decoding as UTF-8 text first
                try:
                    text = field_data.decode('utf-8')
                    # Check if it looks like readable text (not binary protobuf)
                    printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\r\t') / max(len(text), 1)
                    if printable_ratio > 0.8 and len(text) > 0:
                        return text
                except UnicodeDecodeError:
                    pass

                # If not text, it's an embedded message — recurse
                result = extract_text_from_protobuf(field_data)
                if result:
                    return result

        elif wire_type == 0:  # Varint
            _, i = decode_varint(blob, i)
        elif wire_type == 1:  # 64-bit fixed
            i += 8
        elif wire_type == 5:  # 32-bit fixed
            i += 4
        else:
            break

    return None


def main():
    parser = argparse.ArgumentParser(description='Extract sent messages from Signal MSL backup')
    parser.add_argument('--db', required=True, help='Path to exported Signal database')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    args = parser.parse_args()

    DB_PATH = args.db
    OUTPUT = args.output

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get recipient info for context
    c.execute("""
        SELECT DISTINCT mr.recipient_id, r.e164, r.profile_given_name, 
               r.system_joined_name, r.nickname_joined_name
        FROM msl_recipient mr
        JOIN recipient r ON r._id = mr.recipient_id
    """)
    recipients = {}
    for row in c.fetchall():
        recipients[row[0]] = {
            "phone": row[1],
            "profile_name": row[2],
            "system_name": row[3],
            "nickname": row[4]
        }
    print(f"Recipients in MSL: {json.dumps(recipients, indent=2)}")

    # Extract all messages
    c.execute("""
        SELECT p._id, p.date_sent, p.content, p.content_hint, p.urgent,
               GROUP_CONCAT(mr.recipient_id) as recipient_ids
        FROM msl_payload p
        LEFT JOIN msl_recipient mr ON mr.payload_id = p._id
        GROUP BY p._id
        ORDER BY p.date_sent ASC
    """)

    messages = []
    text_count = 0
    empty_count = 0
    total = 0

    for row in c.fetchall():
        total += 1
        payload_id, date_sent, content, content_hint, urgent, recipient_ids_str = row

        ts = datetime.fromtimestamp(date_sent / 1000)
        body = extract_text_from_protobuf(content) if content else None

        msg = {
            "id": payload_id,
            "timestamp": date_sent,
            "datetime": ts.strftime('%Y-%m-%d %H:%M:%S'),
            "date": ts.strftime('%Y-%m-%d'),
            "time": ts.strftime('%H:%M:%S'),
            "direction": "sent",  # MSL = Message Send Log = outgoing only
            "body": body,
            "has_text": body is not None and len(body.strip()) > 0,
            "content_hint": content_hint,
            "urgent": urgent,
            "blob_size": len(content) if content else 0,
            "recipient_ids": [int(x) for x in recipient_ids_str.split(',')] if recipient_ids_str else []
        }
        messages.append(msg)

        if body and len(body.strip()) > 0:
            text_count += 1
        else:
            empty_count += 1

    conn.close()

    # Summary
    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"Total MSL payloads: {total}")
    print(f"With readable text: {text_count}")
    print(f"Without text (media/receipts/reactions): {empty_count}")

    if messages:
        first = messages[0]['datetime']
        last = messages[-1]['datetime']
        print(f"Date range: {first} → {last}")

    # Count by date
    from collections import Counter
    daily = Counter(m['date'] for m in messages if m['has_text'])
    print(f"\nMessages with text by date:")
    for date in sorted(daily.keys()):
        print(f"  {date}: {daily[date]}")

    # Save
    output_data = {
        "extraction_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source": "Signal MSL (Message Send Log) - YOUR SENT MESSAGES ONLY",
        "recipients": recipients,
        "summary": {
            "total_payloads": total,
            "with_text": text_count,
            "without_text": empty_count,
            "date_range": {
                "first": messages[0]['datetime'] if messages else None,
                "last": messages[-1]['datetime'] if messages else None,
            }
        },
        "messages": messages
    }

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {OUTPUT}")


if __name__ == '__main__':
    main()
