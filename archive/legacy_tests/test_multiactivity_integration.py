"""
複数アクティビティの登録・統合テスト（Form形式）
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# テスト用メンバー: 複数アクティビティを持つ（Form形式）
timestamp = datetime.now().strftime('%H%M%S')

form_data = {
    "名前": f"テスト太郎_{timestamp}",
    "会社名": "テスト会社",
    "業種カテゴリ": "IT・システム開発",
    "業種詳細": "Web開発ツール",
    "事業フェーズ": "成長期",
    # Activity 1
    "活動1_名称": "Web開発サービス",
    "活動1_サービス": "React/Node.js によるWeb開発。フロントエンド・バックエンド両対応。",
    "活動1_対象業界": "SaaS, 金融",
    "活動1_対象企業規模": "中小企業10〜300名",
    "活動1_強み詳細": "フロントエンド・バックエンド両対応。モダンなWeb技術スタックでの開発実績。",
    "活動1_課題詳細": "大規模運用の経験不足。スケーラビリティ対応の知見が必要。",
    "活動1_強み": ["技術・開発"],
    "活動1_課題": ["営業・マーケティング"],
    "活動1_ポジション": ["制作・開発・導入", "運用・保守・継続支援"],
    # Activity 2
    "活動2_名称": "マーケティングコンサル",
    "活動2_サービス": "デジタルマーケティング戦略コンサル。SEO・SEM・コンテンツマーケティング。",
    "活動2_対象業界": "B2B SaaS, 教育",
    "活動2_対象企業規模": "中小企業10〜300名",
    "活動2_強み詳細": "SEO・SEM・コンテンツマーケティング。業界別のマーケティング戦略。",
    "活動2_課題詳細": "営業プロセスの自動化未対応。セールスチーム構築が課題。",
    "活動2_強み": ["業界知見"],
    "活動2_課題": ["営業ネットワーク"],
    "活動2_ポジション": ["集客・マーケティング"],
    # Activity 3
    "活動3_名称": "企画・PMO",
    "活動3_サービス": "プロダクト企画・PMOサービス。ロードマップ策定・優先順位付け。",
    "活動3_対象業界": "テクノロジー, 金融テック",
    "活動3_対象企業規模": "大企業300名〜",
    "活動3_強み詳細": "ロードマップ策定・優先順位付け。プロダクト戦略コンサル。",
    "活動3_課題詳細": "エンジニア採用支援が必要。開発リソースの確保。",
    "活動3_強み": ["ブランド"],
    "活動3_課題": ["資金・リソース"],
    "活動3_ポジション": ["経営・戦略・資金調達"],
}

print("=" * 60)
print("複数アクティビティ登録テスト（Form形式）")
print("=" * 60)
print(f"\nテストメンバー: {form_data['名前']}")
print(f"アクティビティ数: 3")

try:
    # Step 1: メンバー登録
    print("\n[Step 1] メンバー登録（3つのアクティビティ付き）...")
    res = requests.post(
        f"{BASE_URL}/api/register-multiactivity",
        data=form_data,
        timeout=15
    )
    print(f"  Status: {res.status_code}")

    if res.status_code != 200:
        print(f"  ERROR: {res.text}")
        exit(1)

    result = res.json()
    page_id = result.get("page_id")
    print(f"  [OK] メンバー登録成功: {page_id}")

    # Step 2: 登録結果確認（API から）
    print("\n[Step 2] 登録統計を確認...")
    res = requests.get(f"{BASE_URL}/api/stats", timeout=10)
    if res.status_code == 200:
        stats_response = res.json()
        # 複数の応答形式に対応
        if 'stats' in stats_response:
            stats = stats_response['stats']
        else:
            stats = stats_response
        print(f"  総登録者数: {stats.get('総登録者数', stats.get('total_members', 0))}")
        print(f"  マッチング可能件数: {stats.get('マッチング可能件数', stats.get('matchable_count', 0))}")
    else:
        print(f"  Warning: stats取得失敗 {res.status_code}")

    # Step 3: マッチング実行（複数アクティビティが統合されるか確認）
    print("\n[Step 3] 別のテストメンバーを登録...")
    form_data2 = {
        "名前": f"テスト花子_{timestamp}",
        "会社名": "別テスト会社",
        "業種カテゴリ": "営業・販売支援",
        "業種詳細": "経営コンサル",
        "事業フェーズ": "安定期",
        # Activity 1 only
        "活動1_名称": "営業支援サービス",
        "活動1_サービス": "営業組織構築・営業研修。BtoB営業フロー最適化。",
        "活動1_対象業界": "SaaS, テクノロジー",
        "活動1_対象企業規模": "中小企業10〜300名",
        "活動1_強み詳細": "BtoB営業フロー最適化。営業プロセス改善の実績。",
        "活動1_課題詳細": "リード生成が課題。マーケティング支援が必要。",
        "活動1_強み": ["営業・ネットワーク"],
        "活動1_課題": ["営業・マーケティング"],
        "活動1_ポジション": ["営業・提案・クロージング"],
    }
    res = requests.post(
        f"{BASE_URL}/api/register-multiactivity",
        data=form_data2,
        timeout=15
    )
    if res.status_code == 200:
        print(f"  [OK] 2番目のメンバー登録成功")
    else:
        print(f"  ERROR: {res.text}")

    # Step 4: マッチング実行
    print("\n[Step 4] マッチング実行...")
    res = requests.post(
        f"{BASE_URL}/api/run-matching",
        json={"max_matches": 5},
        timeout=120
    )

    if res.status_code == 200:
        result = res.json()
        print(f"  [OK] マッチング実行成功")

        # 応答形式を確認
        if "results" in result:
            matches = result["results"].get("matched", [])
        elif "結果" in result:
            matches = result["結果"]
        else:
            matches = []

        if matches:
            print(f"  マッチング件数: {len(matches)}")
            # マッチング結果を検査
            for i, match in enumerate(matches[:3], 1):
                member_a = match.get('メンバーA名', match.get('member_a'))
                member_b = match.get('メンバーB名', match.get('member_b'))
                score = match.get('スコア', match.get('score', 'N/A'))
                reason = match.get('マッチング理由', match.get('reason', ''))

                print(f"\n  [{i}] {member_a} × {member_b}")
                print(f"      スコア: {score}")
                if reason:
                    print(f"      マッチング理由: {reason[:80]}...")
        else:
            print(f"  マッチング結果がありません（十分なメンバーがいない可能性があります）")
    else:
        print(f"  ERROR: {res.status_code}")
        print(f"  {res.text}")

    print("\n" + "=" * 60)
    print("[OK] テスト完了")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
