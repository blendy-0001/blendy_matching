#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

# .env ファイル読み込み
env_path = Path(".env")
if env_path.exists():
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip('"').strip("'")

from notion_client import get_all_members, get_activities_for_member

members = get_all_members()
print(f"メンバー数: {len(members)}")

if members:
    print(f"\n最初のメンバー:")
    print(f"  名前: {members[0].get('名前', 'N/A')}")
    print(f"  会社名: {members[0].get('会社名', 'N/A')}")
    print(f"  業種カテゴリ: {members[0].get('業種カテゴリ', 'N/A')}")
    print(f"  事業フェーズ: {members[0].get('事業フェーズ', 'N/A')}")
    print(f"  プロパティキー: {list(members[0].keys())}")

    # Activities データも確認
    member_name = members[0].get("名前")
    if member_name:
        print(f"\n{member_name} のアクティビティ:")
        activities = get_activities_for_member(member_name)
        print(f"  アクティビティ数: {len(activities)}")
        if activities:
            print(f"  最初のアクティビティ: {activities[0]}")
else:
    print("メンバーなし")
