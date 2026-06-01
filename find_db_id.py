import requests
import json

NOTION_API_KEY = "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"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2026-03-11",
}

print("[*] Searching for databases in Notion workspace...")

# Method 1: Try to list databases
try:
    response = requests.post(
        "https://api.notion.com/v1/search",
        headers=HEADERS,
        json={"filter": {"value": "database", "property": "object"}},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Found {len(data.get('results', []))} databases:")
        for db in data.get('results', [])[:10]:
            print(f"  - {db.get('title', 'Untitled')}")
            print(f"    ID: {db.get('id')}")
    else:
        print(f"[ERROR] Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"[ERROR] {e}")

# Method 2: List recent pages
print("\n[*] Listing recent pages/databases...")
try:
    response = requests.get(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text[:300]}")
except Exception as e:
    print(f"[ERROR] {e}")
