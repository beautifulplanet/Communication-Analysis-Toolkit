import argparse
import os


def redact_files(target_dir, phone_number):
    redaction = "[REDACTED_NUMBER]"
    print(f"Scanning {target_dir} for phone number...")
    count = 0

    for filename in os.listdir(target_dir):
        filepath = os.path.join(target_dir, filename)

        if os.path.isfile(filepath):
            try:
                with open(filepath, encoding='utf-8') as f:
                    content = f.read()

                if phone_number in content:
                    print(f"Redacting from {filename}...")
                    new_content = content.replace(phone_number, redaction)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
            except Exception as e:
                print(f"Could not process {filename}: {e}")

    print(f"Finished. Redacted number from {count} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Redact a phone number from files in a directory')
    parser.add_argument('--dir', required=True, help='Directory to scan')
    parser.add_argument('--phone', required=True, help='Phone number to redact')
    args = parser.parse_args()
    redact_files(args.dir, args.phone)
