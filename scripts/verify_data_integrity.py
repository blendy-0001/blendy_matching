#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify data integrity: members and activities are correctly linked
"""
import sys
sys.path.insert(0, '.')

from notion_client import get_all_members
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('NOTION_API_KEY')
ACTIVITIES_DB_ID = os.getenv('ACTIVITIES_DB_ID')

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Notion-Version': '2022-06-28',
}

def get_all_activities():
    """Get all activities from the database"""
    activities = []
    url = f'https://api.notion.com/v1/databases/{ACTIVITIES_DB_ID}/query'
    payload = {}

    while True:
        try:
            res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()

            for page in data.get('results', []):
                props = page['properties']
                activity_name = props.get('アクティビティ名', {}).get('title', [])
                activity_name_text = ''.join(t.get('plain_text', '') for t in activity_name)
                member_relation = props.get('メンバー', {}).get('relation', [])
                member_id = member_relation[0]['id'] if member_relation else None

                activities.append({
                    'id': page['id'],
                    'name': activity_name_text,
                    'member_id': member_id
                })

            if not data.get('has_more'):
                break
            payload['start_cursor'] = data['next_cursor']

        except Exception as e:
            print(f'Error fetching activities: {e}')
            break

    return activities

print("=" * 70)
print("DATA INTEGRITY VERIFICATION")
print("=" * 70)
print()

# Get all members
members = get_all_members()
print(f"Total members: {len(members)}")

# Get all activities
activities = get_all_activities()
print(f"Total activities: {len(activities)}")
print()

# Count test companies
test_members = [m for m in members if m.get('会社名', '').startswith('Test Company')]
test_companies_set = set(m.get('会社名', '') for m in test_members)
print(f"Test companies: {len(test_companies_set)}")
print()

# Check activity linkage
print("ACTIVITY LINKAGE CHECK")
print("-" * 70)

activities_by_member = {}
for activity in activities:
    member_id = activity['member_id']
    if member_id:
        if member_id not in activities_by_member:
            activities_by_member[member_id] = []
        activities_by_member[member_id].append(activity['name'])

test_company_ids = set(m['id'] for m in test_members)
activities_with_test_members = {m_id: acts for m_id, acts in activities_by_member.items()
                                if m_id in test_company_ids}

print(f"Test companies with linked activities: {len(activities_with_test_members)}")
print()

# Show details
if activities_with_test_members:
    print("Sample activities for test companies:")
    for i, (member_id, activity_list) in enumerate(list(activities_with_test_members.items())[:5]):
        # Find the member name
        member_name = next((m.get('会社名', 'Unknown') for m in test_members if m['id'] == member_id), 'Unknown')
        print(f"  {member_name}:")
        for activity in activity_list:
            print(f"    - {activity}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

test_members_with_activities = len(activities_with_test_members)
total_test_members = len(test_members)

if test_members_with_activities == total_test_members:
    print(f"✓ All {total_test_members} test members have linked activities")
else:
    missing = total_test_members - test_members_with_activities
    print(f"✗ {missing}/{total_test_members} test members are missing activities")

print()
total_test_activities = sum(len(acts) for acts in activities_with_test_members.values())
print(f"Total activities for test companies: {total_test_activities}")
print(f"Average activities per test company: {total_test_activities/total_test_members:.1f}" if total_test_members > 0 else "N/A")
