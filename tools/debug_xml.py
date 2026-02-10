
import xml.etree.ElementTree as ET
try:
    import defusedxml.ElementTree as SafeET
except ImportError:
    SafeET = None
import os
import sys
import argparse

parser = argparse.ArgumentParser(description='Debug/validate an SMS XML backup file')
parser.add_argument('xml_file', help='Path to SMS XML file')
args = parser.parse_args()
SMS_XML = args.xml_file

try:
    print(f"Parsing {SMS_XML}...")
    _parse = SafeET.parse if SafeET else ET.parse
    tree = _parse(SMS_XML)
    root = tree.getroot()
    count = 0
    for sms in root.findall('sms'):
        count += 1
    print(f"Parsed {count} messages successfully.")
except Exception as e:
    print(f"Error: {e}")
