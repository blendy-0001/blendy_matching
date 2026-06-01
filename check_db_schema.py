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

db_url = f'https://api.notion.com/v1/databases/{MEMBERS_DB_ID}'
response = requests.get(db_url, headers=HEADERS, timeout=10)
data = response.json()

print("Database Properties Schema:")
print("=" * 60)
for prop_name, prop_config in data.get('properties', {}).items():
    prop_type = prop_config.get('type', 'unknown')
    is_primary = '(TITLE)' if prop_config.get('is_inline') == False and prop_type == 'title' else ''

    # Print with sanitized name
    try:
        print(f"{prop_name:20} -> {prop_type:15} {is_primary}")
    except:
        print(f"[property]:20 -> {prop_type:15}")

# Save raw properties to file
with open('db_schema.json', 'w', encoding='utf-8') as f:
    props_info = {}
    for prop_name, prop_config in data.get('properties', {}).items():
        props_info[prop_name] = {
            'type': prop_config.get('type'),
            'config': str(prop_config)[:200]
        }
    json.dump(props_info, f, ensure_ascii=False, indent=2)

print()
print("Properties saved to db_schema.json")
