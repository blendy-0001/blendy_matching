#!/usr/bin/env python
"""
Test create_member directly with the exact data from the endpoint
"""
import sys
sys.path.insert(0, '.')

from notion_client import create_member
import traceback

# Exact data that would be passed from the endpoint
member_data = {
    "名前": "Test Person",  # from 代表者名 or 会社名
    "会社名": "Test Company Ltd",
    "業種カテゴリ": "IT・システム開発",  # extracted from form
    "事業フェーズ": "成長期",  # extracted from form
    "協業タイプ": "",
}

print("Testing create_member with endpoint data...")
print(f"member_data: {member_data}")
print()

try:
    member_id = create_member(member_data)
    print(f"Success! member_id: {member_id}")
except Exception as e:
    print(f"Exception: {type(e).__name__}")
    print(f"Message: {e}")
    print()
    print("Full traceback:")
    print(traceback.format_exc())
