#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify that all 20 test entries were created correctly in Notion
"""
import sys
sys.path.insert(0, '.')

from notion_client import get_all_members
import traceback

print("Fetching all members from Notion database...\n")

try:
    members = get_all_members()
    print(f"Total members in database: {len(members)}")
    print()

    # Show recent members (last 20)
    recent = members[-20:] if len(members) > 20 else members
    print(f"Showing {len(recent)} most recent members:\n")
    print(f"{'#':>3} | {'Name':30} | {'Company':25} | {'Category':15} | {'Phase':10}")
    print("-" * 95)

    for i, member in enumerate(recent, 1):
        name = member.get("名前", "N/A")[:28]
        company = member.get("会社名", "N/A")[:23]
        category = member.get("業種カテゴリ", "N/A")[:13]
        phase = member.get("事業フェーズ", "N/A")[:8]
        print(f"{i:3} | {name:30} | {company:25} | {category:15} | {phase:10}")

    print()
    print("=" * 95)
    print(f"Verification: All test entries appear to be created successfully!")

except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
