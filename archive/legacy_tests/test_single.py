import requests
import json

BASE_URL = "http://localhost:8000"

form_data = {
    "代表者名": "Test Person",
    "会社名": "Test Company Ltd",
    "業種カテゴリ": "IT・システム開発",
    "業種詳細": "Software Development",
    "事業フェーズ": "成長期",
    "活動1_名称": "Activity 1",
    "活動1_サービス": "Service Description",
    "活動1_強み詳細": "We have strong expertise",
    "活動1_課題詳細": "We need to scale",
    "活動1_対象業界": "Finance",
    "活動1_対象規模": "Large",
}

print(f"Sending form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
print()

response = requests.post(
    f"{BASE_URL}/api/register-multiactivity",
    data=form_data,
    timeout=10
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
print()

if response.status_code == 200:
    data = response.json()
    print(f"JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")
