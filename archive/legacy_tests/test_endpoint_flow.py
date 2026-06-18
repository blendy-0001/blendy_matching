#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Replicate exact endpoint flow step-by-step
"""
import sys
sys.path.insert(0, '.')

from notion_client import create_member, create_activity
import traceback

# Step 1: Simulate form data parsing (exact same as endpoint)
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

# Step 2: Extract basic member info (exactly as endpoint does)
会社名 = form_data.get("会社名", "").strip()
事業フェーズ = form_data.get("事業フェーズ", "").strip()
業種カテゴリ = form_data.get("業種カテゴリ", "").strip()
代表者名 = form_data.get("代表者名", "").strip()
名前 = 代表者名 or 会社名

print("Step 1: Form parsing")
print(f"  Name: {repr(名前)}")
print(f"  Company: {repr(会社名)}")
print(f"  Category: {repr(業種カテゴリ)}")
print(f"  Phase: {repr(事業フェーズ)}")
print()

# Step 3: Build member_data (exactly as endpoint does)
member_data = {
    "名前": 名前,
    "会社名": 会社名,
    "業種カテゴリ": 業種カテゴリ,
    "事業フェーズ": 事業フェーズ,
    "協業タイプ": "",
}

print("Step 2: member_data prepared")
print(f"  Keys: {list(member_data.keys())}")
print()

# Step 4: Call create_member
print("Step 3: Calling create_member...")
try:
    member_id = create_member(member_data)
    if member_id:
        print(f"  OK! member_id: {member_id[:20]}...")
    else:
        print(f"  EMPTY RESULT")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    import sys
    traceback.print_exc(file=sys.stdout)
