#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check all members directly from Notion API without status filter
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('NOTION_API_KEY')
MEMBERS_DB_ID = os.getenv('MEMBERS_DB_ID')

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
}

url = f'https://api.notion.com/v1/databases/{MEMBERS_DB_ID}/query'

print('Checking all members without status filter...\n')

all_members = []
payload = {}

while True:
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()

        for page in data.get('results', []):
            props = page['properties']
            name = props.get('名前', {}).get('title', [])
            name_text = ''.join(t.get('plain_text', '') for t in name)
            company = props.get('会社名', {}).get('rich_text', [])
            company_text = ''.join(t.get('plain_text', '') for t in company)
            status = props.get('ステータス', {}).get('select', {}).get('name', 'N/A')

            all_members.append({
                'name': name_text,
                'company': company_text,
                'status': status
            })

        if not data.get('has_more'):
            break
        payload['start_cursor'] = data['next_cursor']

    except Exception as e:
        print(f'Error: {e}')
        break

print(f'Total members in database: {len(all_members)}\n')

# Group by company and status
test_companies = {}
for member in all_members:
    company = member['company']
    if company.startswith('Test Company'):
        if company not in test_companies:
            test_companies[company] = member['status']

test_companies = dict(sorted(test_companies.items(),
                             key=lambda x: int(x[0].split()[-1])))

print(f'Test companies found: {len(test_companies)}')
print()
print(f"{'Company':30} | {'Status':15}")
print("-" * 48)
for company, status in test_companies.items():
    print(f"{company:30} | {status:15}")

print()
print(f"Summary: {len(test_companies)}/20 test companies created")
if len(test_companies) < 20:
    print(f"Missing: {20 - len(test_companies)} companies")
    created = set(f"Test Company {i}" for i in range(1, 21))
    found = set(test_companies.keys())
    missing = created - found
    print(f"Missing companies: {sorted(missing)}")
