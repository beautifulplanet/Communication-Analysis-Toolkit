import os

import requests
from requests.auth import HTTPBasicAuth

CASES_DIR = "cases"
TEST_ID = "test_delete_case"

def test_deletion():
    # 1. Create dummy case
    case_path = os.path.join(CASES_DIR, TEST_ID)
    os.makedirs(case_path, exist_ok=True)
    with open(os.path.join(case_path, "DATA.json"), "w") as f:
        f.write("{}")

    print(f"Created test case at {case_path}")

    # 2. Delete via API
    auth = HTTPBasicAuth('admin', 'changeme')
    url = f"http://localhost:8003/api/cases/{TEST_ID}"

    print(f"Sending DELETE to {url}...")
    try:
        res = requests.delete(url, auth=auth)
        print(f"Response: {res.status_code}")

        if res.status_code != 204:
            print(f"FAIL: Expected 204, got {res.status_code}")
            return

    except Exception as e:
        print(f"FAIL: Request error: {e}")
        return

    # 3. Verify deletion
    if os.path.exists(case_path):
        print(f"FAIL: Directory {case_path} still exists!")
    else:
        print("SUCCESS: Case directory deleted.")

if __name__ == "__main__":
    if not os.path.exists(CASES_DIR):
        os.makedirs(CASES_DIR)
    test_deletion()
