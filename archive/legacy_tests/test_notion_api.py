import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('NOTION_API_KEY')
MEMBERS_DB_ID = os.getenv('MEMBERS_DB_ID')

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
}

print('Testing Notion API...')
print(f'API Key length: {len(API_KEY)}')
print(f'Members DB ID: {MEMBERS_DB_ID}')
print()

# Get the database
db_url = f'https://api.notion.com/v1/databases/{MEMBERS_DB_ID}'
try:
    response = requests.get(db_url, headers=HEADERS, timeout=10)
    print(f'GET Database Status: {response.status_code}')

    if response.status_code == 200:
        data = response.json()
        props = list(data.get('properties', {}).keys())
        print(f'Properties count: {len(props)}')
        print(f'Properties: {props}')

        # Try to create a test page
        print()
        print('Testing page creation...')

        test_payload = {
            "parent": {"database_id": MEMBERS_DB_ID},
            "properties": {
                "会社名": {"title": [{"text": {"content": "Test Company"}}]},
                "ステータス": {"select": {"name": "アクティブ"}}
            }
        }

        create_url = 'https://api.notion.com/v1/pages'
        create_response = requests.post(create_url, headers=HEADERS, json=test_payload, timeout=10)
        print(f'POST Page Status: {create_response.status_code}')

        if create_response.status_code != 200:
            print(f'Error Response: {create_response.text[:500]}')
        else:
            print('Page created successfully!')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
