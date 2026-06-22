"""
マルチアクティビティ登録フォームのテストデータを自動生成
20件のメンバーを登録し、各メンバーに1～3個のアクティビティを追加
"""
import requests
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

# テストデータ定義
companies = [
    {"name": "Test Company A", "company": "Digital Marketing Inc"},
    {"name": "Test Company B", "company": "Software Dev Studio"},
    {"name": "Test Company C", "company": "Consulting Partners"},
    {"name": "Test Company D", "company": "Data Analytics Lab"},
    {"name": "Test Company E", "company": "Sales Support Systems"},
    {"name": "Test Company F", "company": "UI/UX Design Studio"},
    {"name": "Test Company G", "company": "Cloud Solutions Ltd"},
    {"name": "Test Company H", "company": "Mobile App Dev"},
    {"name": "Test Company I", "company": "Security Center"},
    {"name": "Test Company J", "company": "AI/ML Platform"},
    {"name": "Test Company K", "company": "ERP Consulting"},
    {"name": "Test Company L", "company": "CRM Planning"},
    {"name": "Test Company M", "company": "Web Marketing Agency"},
    {"name": "Test Company N", "company": "Data Security Solutions"},
    {"name": "Test Company O", "company": "IoT Development"},
    {"name": "Test Company P", "company": "Blockchain Research"},
    {"name": "Test Company Q", "company": "RPA Automation"},
    {"name": "Test Company R", "company": "Customer Success Support"},
    {"name": "Test Company S", "company": "Digital Content Creation"},
    {"name": "Test Company T", "company": "Business Intelligence Tools"},
]

activities_templates = [
    {
        "name": "SaaS Sales Support",
        "service": "Sales automation and CRM implementation",
        "strengths": ["Sales optimization", "CRM setup"],
        "strengths_detail": "15 years of experience with 100+ CRM implementations",
        "challenges": ["Custom integration", "Multi-language support"],
        "challenges_detail": "Global rollout requires multi-language capability",
        "value_chain": ["Sales", "Implementation"],
        "target_industry": "IT / SaaS",
        "target_size": "Mid to Large",
    },
    {
        "name": "Digital Transformation",
        "service": "DX strategy and system implementation",
        "strengths": ["Strategy planning", "Tech selection"],
        "strengths_detail": "10+ years working with Fortune 500 DX projects",
        "challenges": ["Legacy integration", "Change management"],
        "challenges_detail": "Managing parallel legacy system integration is challenging",
        "value_chain": ["Strategy", "Implementation"],
        "target_industry": "Finance / Manufacturing / Retail",
        "target_size": "Large Enterprise",
    },
    {
        "name": "Cloud Migration",
        "service": "On-premise to cloud migration",
        "strengths": ["Cloud implementation", "Cost optimization"],
        "strengths_detail": "AWS, Azure, GCP - all platforms covered",
        "challenges": ["Security", "Zero-downtime migration"],
        "challenges_detail": "24/7 service requires zero-downtime migration",
        "value_chain": ["Infrastructure", "Operations"],
        "target_industry": "All Industries",
        "target_size": "Small to Large",
    },
    {
        "name": "Data Analytics BI",
        "service": "Data warehouse and BI implementation",
        "strengths": ["Data modeling", "Visualization"],
        "strengths_detail": "Tableau, Power BI, Looker - 100+ implementations",
        "challenges": ["Large data processing", "Real-time analytics"],
        "challenges_detail": "Petabyte-scale real-time analytics in progress",
        "value_chain": ["Analytics"],
        "target_industry": "Finance / Retail / Media",
        "target_size": "Mid to Large",
    },
    {
        "name": "AI/ML Implementation",
        "service": "Predictive models and recommendation engines",
        "strengths": ["Model development", "MLOps automation"],
        "strengths_detail": "Python stack expertise with MLOps infrastructure",
        "challenges": ["Model accuracy", "Production deployment"],
        "challenges_detail": "A/B testing and continuous learning pipeline setup",
        "value_chain": ["Research", "Operations"],
        "target_industry": "IT / Finance / E-commerce",
        "target_size": "Startup to Enterprise",
    },
]

def create_test_entries():
    """Create 20 test entries"""
    success_count = 0
    error_count = 0

    for i, company_info in enumerate(companies, 1):
        # Determine activity count: 1-3
        activity_count = 1 + (i % 3)

        # Build form data - use correct Japanese field names
        # Valid options for 業種カテゴリ: IT・システム開発, マーケティング・広告, コンサルティング, 営業・販売支援, 教育・研修, 医療・福祉・介護, 製造・メーカー, 不動産・建設, 士業, クリエイティブ, その他
        # Valid options for 事業フェーズ: アイデア段階, 立上げ期, 成長期, 安定期
        form_data = {
            "代表者名": company_info["name"],
            "会社名": company_info["company"],
            "業種カテゴリ": "IT・システム開発" if i % 2 == 0 else "コンサルティング",
            "業種詳細": "Technology and consulting services",
            "事業フェーズ": ["成長期", "立上げ期", "安定期"][i % 3],
        }

        # Add activities (1-3)
        for activity_num in range(1, activity_count + 1):
            activity = activities_templates[(i + activity_num) % len(activities_templates)]

            form_data[f"活動{activity_num}_名称"] = activity["name"]
            form_data[f"活動{activity_num}_サービス"] = activity["service"]
            form_data[f"活動{activity_num}_強み詳細"] = activity["strengths_detail"]
            form_data[f"活動{activity_num}_課題詳細"] = activity["challenges_detail"]
            form_data[f"活動{activity_num}_対象業界"] = activity["target_industry"]
            form_data[f"活動{activity_num}_対象規模"] = activity["target_size"]

            # Checkboxes - form.getlist() handles multiple values
            # We need to add each as a separate form value
            # Note: For proper multipart/form-data, we need to handle lists differently
            for strength in activity["strengths"]:
                if f"活動{activity_num}_強み" not in form_data:
                    form_data[f"活動{activity_num}_強み"] = []
                if not isinstance(form_data[f"活動{activity_num}_強み"], list):
                    form_data[f"活動{activity_num}_強み"] = [form_data[f"活動{activity_num}_強み"]]
                form_data[f"活動{activity_num}_強み"].append(strength)

            for challenge in activity["challenges"]:
                if f"活動{activity_num}_課題" not in form_data:
                    form_data[f"活動{activity_num}_課題"] = []
                if not isinstance(form_data[f"活動{activity_num}_課題"], list):
                    form_data[f"活動{activity_num}_課題"] = [form_data[f"活動{activity_num}_課題"]]
                form_data[f"活動{activity_num}_課題"].append(challenge)

            for vc in activity["value_chain"]:
                if f"活動{activity_num}_ポジション" not in form_data:
                    form_data[f"活動{activity_num}_ポジション"] = []
                if not isinstance(form_data[f"活動{activity_num}_ポジション"], list):
                    form_data[f"活動{activity_num}_ポジション"] = [form_data[f"活動{activity_num}_ポジション"]]
                form_data[f"活動{activity_num}_ポジション"].append(vc)

        # POST to API
        try:
            response = requests.post(
                f"{BASE_URL}/api/register-multiactivity",
                data=form_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"[OK] [{i:2d}] {company_info['name']} - {activity_count} activities")
                    success_count += 1
                else:
                    print(f"[NG] [{i:2d}] {company_info['name']} - Error: {data.get('error')}")
                    error_count += 1
            else:
                print(f"[NG] [{i:2d}] {company_info['name']} - HTTP {response.status_code}: {response.text[:100]}")
                error_count += 1

        except Exception as e:
            print(f"[NG] [{i:2d}] {company_info['name']} - Exception: {str(e)[:100]}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"Result: Success {success_count}, Error {error_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("Starting test data generation...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    create_test_entries()
