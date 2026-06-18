import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('NOTION_API_KEY')
MEMBERS_DB_ID = os.getenv('MEMBERS_DB_ID')

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
}

print('Testing correct payload (matching create_member)...')

# Match the actual create_member payload structure
test_payload = {
    "parent": {"database_id": MEMBERS_DB_ID},
    "properties": {
        "名前": {"title": [{"text": {"content": "Test Person"}}]},
        "会社名": {"rich_text": [{"text": {"content": "Test Company Ltd"}}]},
        "業種カテゴリ": {"select": {"name": "IT・システム開発"}},
        "業種詳細": {"rich_text": [{"text": {"content": "Software Development"}}]},
        "主力サービス": {"rich_text": [{"text": {"content": ""}}]},
        "事業フェーズ": {"select": {"name": "成長期"}},
        "ステータス": {"select": {"name": "アクティブ"}},
    }
}

url = 'https://api.notion.com/v1/pages'
try:
    response = requests.post(url, headers=HEADERS, json=test_payload, timeout=10)
    print(f'Status Code: {response.status_code}')

    if response.status_code != 200:
        error_text = response.text[:800]
        print(f'Error Response: {error_text}')

        # Save to file for easier reading
        with open('error_response.txt', 'w', encoding='utf-8') as f:
            f.write(error_text)
        print('Error saved to error_response.txt')
    else:
        print('SUCCESS! Page created.')
        print(f'Page ID: {response.json().get("id")}')

except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()
