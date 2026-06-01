"""
テスト用メンバーデータ15件を Notion に登録
"""
import requests

# Notion API 設定
NOTION_API_KEY = "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"
MEMBERS_DB_ID = "517b9ae4-8e9d-496d-b581-927bde2af2fe"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# テストメンバーデータ（15件）
test_members = [
    {"name": "鈴木（マーケ支援）", "company": "Marketing Support AE", "industry": "マーケティング", "service": "マーケティング支援・数値分析", "strength": "分析・最適化", "gap": "営業実行", "client_industry": "SaaS・IT", "client_scale": "スタートアップ", "value_chain": ["集客・マーケティング"], "asset": ["マーケティング人材"]},
    {"name": "田中（バックオフィス）", "company": "Back Office Solutions", "industry": "バックオフィス", "service": "経理・労務・総務支援", "strength": "事務効率化", "gap": "営業戦略", "client_industry": "全業種", "client_scale": "中小企業", "value_chain": ["運用・保守・継続支援"], "asset": ["事務人材"]},
    {"name": "佐藤（人事評価）", "company": "HR Systems", "industry": "HRテック", "service": "人事評価システム・研修", "strength": "HR知識・システム", "gap": "営業", "client_industry": "全業種", "client_scale": "中堅企業", "value_chain": ["制作・開発・導入"], "asset": ["HR専門家"]},
    {"name": "木村（営業戦略）", "company": "Sales Strategy Consulting", "industry": "営業代理", "service": "営業戦略・営業研修", "strength": "営業戦略・人材育成", "gap": "技術開発", "client_industry": "全業種", "client_scale": "中堅企業", "value_chain": ["営業・提案・クロージング"], "asset": ["営業コンサルタント"]},
    {"name": "山本（カスタマー対応）", "company": "Customer Experience Center", "industry": "カスタマーサクセス", "service": "コールセンター・顧客対応", "strength": "顧客対応・教育", "gap": "システム構築", "client_industry": "全業種", "client_scale": "中小企業", "value_chain": ["運用・保守・継続支援"], "asset": ["対応チーム"]},
    {"name": "田村（プロダクト管理）", "company": "Product Management Office", "industry": "IT・SaaS", "service": "プロダクト管理・UX最適化", "strength": "プロダクト思考・分析", "gap": "営業・マーケティング", "client_industry": "SaaS・IT", "client_scale": "スタートアップ", "value_chain": ["制作・開発・導入"], "asset": ["PM人材"]},
    {"name": "鈴木（業務自動化）", "company": "Business Process Automation", "industry": "IT・SaaS", "service": "業務自動化・RPA導入", "strength": "自動化技術・プロセス改善", "gap": "営業", "client_industry": "製造・金融", "client_scale": "大企業", "value_chain": ["制作・開発・導入"], "asset": ["エンジニア"]},
    {"name": "鶴田（コンテンツマーケ）", "company": "Content Marketing Agency", "industry": "マーケティング", "service": "コンテンツ制作・SEO対策", "strength": "コンテンツ制作・SEO", "gap": "営業", "client_industry": "全業種", "client_scale": "中小企業", "value_chain": ["認知・ブランディング"], "asset": ["ライター・編集者"]},
    {"name": "中村（顧客分析）", "company": "Customer Analytics Solutions", "industry": "データ分析", "service": "顧客分析・マーケティング分析", "strength": "データ分析・可視化", "gap": "営業", "client_industry": "EC・小売・金融", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["データサイエンティスト"]},
    {"name": "高橋（ブランドデザイン）", "company": "Brand Design Studio", "industry": "デザイン", "service": "ロゴ・ブランドデザイン", "strength": "クリエイティブ・デザイン", "gap": "営業・マーケティング", "client_industry": "全業種", "client_scale": "スタートアップ", "value_chain": ["認知・ブランディング"], "asset": ["デザイナー"]},
    {"name": "佐々木（法務サポート）", "company": "Legal Support Services", "industry": "法務・コンプライアンス", "service": "契約書作成・法務相談", "strength": "法務知識・リスク管理", "gap": "営業", "client_industry": "全業種", "client_scale": "中堅企業", "value_chain": ["運用・保守・継続支援"], "asset": ["法務専門家"]},
    {"name": "石川（組織開発）", "company": "Organization Development", "industry": "経営コンサル", "service": "組織開発・変革管理", "strength": "組織構築・人材育成", "gap": "実装技術", "client_industry": "大企業", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["OD専門家"]},
    {"name": "渡辺（ブロックチェーン）", "company": "Blockchain Solutions", "industry": "FinTech", "service": "ブロックチェーン開発・コンサル", "strength": "技術力・ブロックチェーン", "gap": "営業・市場化", "client_industry": "金融・テック", "client_scale": "スタートアップ", "value_chain": ["制作・開発・導入"], "asset": ["ブロックチェーン開発者"]},
    {"name": "伊藤（リスク管理）", "company": "Risk Management Consulting", "industry": "経営コンサル", "service": "リスク管理・内部監査", "strength": "リスク分析・管理", "gap": "営業", "client_industry": "金融・製造", "client_scale": "大企業", "value_chain": ["運用・保守・継続支援"], "asset": ["リスク管理者"]},
    {"name": "岡本（サステナ経営）", "company": "Sustainability Management", "industry": "環境・サステナビリティ", "service": "サステナビリティ戦略・報告", "strength": "環境知識・戦略", "gap": "実装", "client_industry": "製造・エネルギー", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["サステナ専門家"]},
]

print(f"[INFO] {len(test_members)}件のテストメンバーを Notion に登録中...\n")

success_count = 0
for i, member in enumerate(test_members, 1):
    payload = {
        "parent": {"database_id": MEMBERS_DB_ID},
        "properties": {
            "名前": {"title": [{"text": {"content": member["name"]}}]},
            "会社名": {"rich_text": [{"text": {"content": member["company"]}}]},
            "業種カテゴリ": {"select": {"name": member["industry"]}},
            "業種詳細": {"rich_text": [{"text": {"content": member["industry"]}}]},
            "主力サービス": {"rich_text": [{"text": {"content": member["service"]}}]},
            "エンドクライアント業界": {"rich_text": [{"text": {"content": member["client_industry"]}}]},
            "エンドクライアント規模": {"select": {"name": member["client_scale"]}},
            "クライアントの課題": {"rich_text": [{"text": {"content": "新規開拓"}}]},
            "バリューチェーン位置": {"multi_select": [{"name": vc} for vc in member["value_chain"]]},
            "強み": {"rich_text": [{"text": {"content": member["strength"]}}]},
            "課題・足りないもの": {"rich_text": [{"text": {"content": member["gap"]}}]},
            "保有アセット": {"multi_select": [{"name": asset} for asset in member["asset"]]},
            "事業フェーズ": {"select": {"name": "成長期"}},
            "ステータス": {"select": {"name": "アクティブ"}},
        }
    }

    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload).json()
        if "id" in res:
            print(f"[OK] {i:2d}. {member['name']}")
            success_count += 1
        else:
            print(f"[ERROR] {i:2d}. {member['name']} - エラー: {res.get('message', 'Unknown')}")
    except Exception as e:
        print(f"[ERROR] {i:2d}. {member['name']} - {str(e)}")

print(f"\n[DONE] {success_count}/{len(test_members)}件のメンバー登録が完了しました！")
