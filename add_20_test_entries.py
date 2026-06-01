#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add 20 test company entries via the registration endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test data for 20 different companies
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
    {
        "name": "Test Company 8",
        "category": "教育・研修",
        "phase": "初期段階",
        "detail": "Online Learning Platform",
        "activity": "オンライン教育プラットフォーム",
    },
    {
        "name": "Test Company 9",
        "category": "医療・ヘルスケア",
        "phase": "成長期",
        "detail": "Healthcare IT Solutions",
        "activity": "医療IT・テレメディシン",
    },
    {
        "name": "Test Company 10",
        "category": "不動産・建設",
        "phase": "拡大期",
        "detail": "PropTech Solutions",
        "activity": "不動産テクノロジー",
    },
    {
        "name": "Test Company 11",
        "category": "IT・システム開発",
        "phase": "成長期",
        "detail": "Mobile App Development",
        "activity": "モバイルアプリ開発",
    },
    {
        "name": "Test Company 12",
        "category": "デジタルマーケティング",
        "phase": "初期段階",
        "detail": "Social Media Services",
        "activity": "SNS・ソーシャルメディア",
    },
    {
        "name": "Test Company 13",
        "category": "コンサルティング",
        "phase": "成長期",
        "detail": "Digital Transformation",
        "activity": "デジタルトランスフォーメーション",
    },
    {
        "name": "Test Company 14",
        "category": "IT・システム開発",
        "phase": "拡大期",
        "detail": "Enterprise Software",
        "activity": "エンタープライズソフトウェア",
    },
    {
        "name": "Test Company 15",
        "category": "人材サービス",
        "phase": "初期段階",
        "detail": "Recruitment Solutions",
        "activity": "採用支援ツール",
    },
    {
        "name": "Test Company 16",
        "category": "製造業",
        "phase": "成長期",
        "detail": "Supply Chain Solutions",
        "activity": "サプライチェーン管理",
    },
    {
        "name": "Test Company 17",
        "category": "金融サービス",
        "phase": "初期段階",
        "detail": "Payment Solutions",
        "activity": "決済・ペイメント",
    },
    {
        "name": "Test Company 18",
        "category": "教育・研修",
        "phase": "成長期",
        "detail": "Corporate Training",
        "activity": "企業研修・人材育成",
    },
    {
        "name": "Test Company 19",
        "category": "医療・ヘルスケア",
        "phase": "拡大期",
        "detail": "Medical Devices",
        "activity": "医療機器・診断",
    },
    {
        "name": "Test Company 20",
        "category": "不動産・建設",
        "phase": "成長期",
        "detail": "Construction Management",
        "activity": "建設管理・プロジェクト管理",
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
        print(f"[NG] {company_data['name']:30} -> Exception: {e}")
        return False

if __name__ == "__main__":
    print(f"Adding {len(test_companies)} test company entries...\n")

    success_count = 0
    for i, company in enumerate(test_companies, 1):
        print(f"[{i:2}/{len(test_companies)}] ", end="")
        if add_entry(company):
            success_count += 1

        # Delay to avoid overwhelming the server
        import time
        time.sleep(2)

    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(test_companies)} entries created successfully")
    print(f"Success rate: {success_count*100//len(test_companies)}%")
