#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test member creation with the fixed fields"""
import sys
sys.path.insert(0, '.')

from notion_client import create_member
import json

# テスト用のメンバーデータ
test_member = {
    "名前": "テスト 太郎",
    "会社名": "テスト株式会社",
    "業種カテゴリ": "IT・システム開発",
    "業種詳細": "SaaS プラットフォーム開発",
    "事業フェーズ": "成長期",
    "LINE ID": "@test_user",
    "Facebook URL": "https://facebook.com/test.user",
}

print("=" * 70)
print("MEMBER CREATION TEST")
print("=" * 70)
print()
print("Testing member data:")
print(json.dumps(test_member, ensure_ascii=False, indent=2))
print()

try:
    member_id = create_member(test_member)
    if member_id:
        print(f"✅ SUCCESS: Member created with ID: {member_id}")
    else:
        print("❌ FAILED: No ID returned")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"   Details: {str(e)[:500]}")
