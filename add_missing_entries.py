#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add the missing test company entries (1-7)
"""
import requests
import time

BASE_URL = "http://localhost:8000"

# Test data for missing companies 1-7
test_companies = [
    {
        "name": "Test Company 1",
        "category": "IT・システム開発",
        "phase": "成長期",
        "detail": "SaaS Platform Development",
        "activity": "クラウドサービス開発",
    },
    {
        "name": "Test Company 2",
        "category": "デジタルマーケティング",
        "phase": "成長期",
        "detail": "Marketing Automation Services",
        "activity": "マーケティングオートメーション",
    },
    {
        "name": "Test Company 3",
        "category": "コンサルティング",
        "phase": "拡大期",
        "detail": "Business Strategy Consulting",
        "activity": "経営コンサルティング",
    },
    {
        "name": "Test Company 4",
        "category": "IT・システム開発",
        "phase": "初期段階",
        "detail": "AI/ML Solutions",
        "activity": "AI・機械学習ソリューション",
    },
    {
        "name": "Test Company 5",
        "category": "人材サービス",
        "phase": "成長期",
        "detail": "HR Tech Platform",
        "activity": "人材採用プラットフォーム",
    },
    {
        "name": "Test Company 6",
        "category": "製造業",
        "phase": "拡大期",
        "detail": "Industrial IoT Solutions",
        "activity": "IoT・スマートファクトリー",
    },
    {
        "name": "Test Company 7",
        "category": "金融サービス",
        "phase": "成長期",
        "detail": "FinTech Solutions",
        "activity": "金融テクノロジー",
    },
]

def add_entry(company_data):
    """Add a single company entry via the form endpoint"""
    form_data = {
        "会社名": company_data["name"],
        "代表者名": f"Representative of {company_data['name']}",
        "業種カテゴリ": company_data["category"],
        "業種詳細": company_data["detail"],
        "事業フェーズ": company_data["phase"],
        "活動1_名称": company_data["activity"],
        "活動1_サービス": f"{company_data['activity']} Services",
        "活動1_強み詳細": "Strong expertise in our field",
        "活動1_課題詳細": "Looking for partners to expand",
        "活動1_対象業界": "All Industries",
        "活動1_対象規模": "Large",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/register-multiactivity",
            data=form_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"[OK] {company_data['name']:30} -> ID: {result['page_id'][:20]}...")
                return True
            else:
                print(f"[NG] {company_data['name']:30} -> Error: {result.get('error')}")
                return False
        else:
            print(f"[NG] {company_data['name']:30} -> HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[NG] {company_data['name']:30} -> Exception: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print(f"Adding missing {len(test_companies)} test company entries (1-7)...\n")

    success_count = 0
    for i, company in enumerate(test_companies, 1):
        print(f"[{i}/{len(test_companies)}] ", end="")
        if add_entry(company):
            success_count += 1
        time.sleep(2)  # Delay to avoid overwhelming server

    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(test_companies)} entries created successfully")
