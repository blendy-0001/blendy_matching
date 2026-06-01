"""
テスト用メンバーデータ30件を Notion に登録
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

# テストメンバーデータ（30件）
test_members = [
    {"name": "太郎（SaaS開発）", "company": "Tech Startup A", "industry": "IT・SaaS", "service": "BtoB SaaS プラットフォーム開発", "strength": "技術力・システム設計", "gap": "営業・マーケティング", "client_industry": "金融・保険", "client_scale": "中堅企業", "value_chain": ["制作・開発・導入"], "asset": ["開発チーム"]},
    {"name": "花子（営業代理）", "company": "Sales Agency B", "industry": "営業代理", "service": "営業代理・新規営業支援", "strength": "営業ネットワーク・人脈", "gap": "技術力・製品開発", "client_industry": "金融・保険", "client_scale": "大企業", "value_chain": ["営業・提案・クロージング"], "asset": ["営業人材"]},
    {"name": "次郎（マーケティング）", "company": "Marketing Firm C", "industry": "マーケティング", "service": "デジタルマーケティング・SEO対策", "strength": "マーケティング・集客", "gap": "開発技術", "client_industry": "EC・小売", "client_scale": "スタートアップ", "value_chain": ["集客・マーケティング"], "asset": ["マーケティング人材"]},
    {"name": "美咲（クラウド提供）", "company": "Cloud Services D", "industry": "IT・SaaS", "service": "クラウドインフラ・運用保守", "strength": "技術力・運用ノウハウ", "gap": "営業", "client_industry": "製造業", "client_scale": "中企業", "value_chain": ["運用・保守・継続支援"], "asset": ["エンジニア"]},
    {"name": "健太（人材紹介）", "company": "HR Consulting E", "industry": "人材紹介", "service": "IT人材紹介・採用支援", "strength": "人脈ネットワーク", "gap": "技術知識", "client_industry": "IT・SaaS", "client_scale": "スタートアップ", "value_chain": ["経営・戦略・資金調達"], "asset": ["人材ネットワーク"]},
    {"name": "由美（デザイン）", "company": "Design Studio F", "industry": "デザイン", "service": "UI/UXデザイン・ブランディング", "strength": "クリエイティブ・デザイン力", "gap": "開発実装", "client_industry": "EC・小売", "client_scale": "スタートアップ", "value_chain": ["認知・ブランディング"], "asset": ["デザイナー"]},
    {"name": "拓也（WEB制作）", "company": "Web Agency G", "industry": "WEB制作", "service": "WEB制作・サイト構築", "strength": "開発・実装", "gap": "営業・集客", "client_industry": "サービス業", "client_scale": "中小企業", "value_chain": ["制作・開発・導入"], "asset": ["開発チーム"]},
    {"name": "智子（コンサル）", "company": "Business Consulting H", "industry": "経営コンサル", "service": "経営戦略・事業開発コンサル", "strength": "戦略思考・分析力", "gap": "実装技術", "client_industry": "製造業", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["コンサルタント"]},
    {"name": "竜一（決済システム）", "company": "FinTech Solutions I", "industry": "FinTech", "service": "決済システム・ウォレット開発", "strength": "技術力・セキュリティ", "gap": "営業・チャネル", "client_industry": "EC・金融", "client_scale": "スタートアップ", "value_chain": ["制作・開発・導入"], "asset": ["エンジニア"]},
    {"name": "優子（イベント企画）", "company": "Event Management J", "industry": "イベント・PR", "service": "イベント企画・ PR支援", "strength": "人脈・ネットワーク", "gap": "技術", "client_industry": "サービス業", "client_scale": "中小企業", "value_chain": ["集客・マーケティング"], "asset": ["営業人材"]},
    {"name": "翔太（AI/ML）", "company": "AI Startup K", "industry": "AI・機械学習", "service": "AI・機械学習モデル開発", "strength": "技術力・データ分析", "gap": "営業・市場調査", "client_industry": "金融・製造", "client_scale": "大企業", "value_chain": ["制作・開発・導入"], "asset": ["データサイエンティスト"]},
    {"name": "美優（業界特化営業）", "company": "Industry Sales L", "industry": "営業代理", "service": "業界特化型営業支援", "strength": "業界知識・営業", "gap": "技術開発", "client_industry": "建設・不動産", "client_scale": "中堅企業", "value_chain": ["営業・提案・クロージング"], "asset": ["営業人材"]},
    {"name": "慎一（セキュリティ）", "company": "Security Firm M", "industry": "IT・セキュリティ", "service": "サイバーセキュリティ・脆弱性診断", "strength": "技術力・セキュリティ", "gap": "営業", "client_industry": "金融・官公庁", "client_scale": "大企業", "value_chain": ["運用・保守・継続支援"], "asset": ["セキュリティエンジニア"]},
    {"name": "菜月（リード獲得）", "company": "Lead Generation N", "industry": "マーケティング", "service": "リード獲得・営業支援", "strength": "営業支援・システム", "gap": "製品開発", "client_industry": "SaaS・IT", "client_scale": "スタートアップ", "value_chain": ["リード獲得・見込み客育成"], "asset": ["マーケティング人材"]},
    {"name": "大樹（物流最適化）", "company": "Logistics Tech O", "industry": "ロジスティクス", "service": "物流最適化・配送管理", "strength": "業界知識・効率化", "gap": "IT技術", "client_industry": "EC・製造", "client_scale": "中堅企業", "value_chain": ["運用・保守・継続支援"], "asset": ["ドメイン知識"]},
    {"name": "恵美（ブランド戦略）", "company": "Brand Strategy P", "industry": "ブランディング", "service": "ブランド戦略・ポジショニング", "strength": "戦略・マーケティング", "gap": "実装", "client_industry": "消費財・小売", "client_scale": "中小企業", "value_chain": ["認知・ブランディング"], "asset": ["企画人材"]},
    {"name": "晋也（動画制作）", "company": "Video Production Q", "industry": "メディア・動画", "service": "動画制作・コンテンツ制作", "strength": "クリエイティブ", "gap": "営業・配信", "client_industry": "サービス業", "client_scale": "スタートアップ", "value_chain": ["認知・ブランディング"], "asset": ["制作チーム"]},
    {"name": "由香（教育プログラム）", "company": "Education Tech R", "industry": "教育", "service": "研修・教育プログラム開発", "strength": "コンテンツ開発・教育", "gap": "営業・配信", "client_industry": "全業種", "client_scale": "中堅企業", "value_chain": ["教育・研修・人材育成"], "asset": ["講師・インストラクター"]},
    {"name": "貴博（不動産仲介）", "company": "Real Estate S", "industry": "不動産", "service": "不動産仲介・投資支援", "strength": "営業・人脈", "gap": "IT・デジタル化", "client_industry": "投資家・企業", "client_scale": "中小企業", "value_chain": ["営業・提案・クロージング"], "asset": ["営業人材"]},
    {"name": "千恵（翻訳・多言語）", "company": "Translation Services T", "industry": "翻訳・グローバル", "service": "翻訳・多言語対応支援", "strength": "言語・グローバル", "gap": "デジタル化", "client_industry": "製造・IT", "client_scale": "中堅企業", "value_chain": ["運用・保守・継続支援"], "asset": ["言語スペシャリスト"]},
    {"name": "勇気（IoTソリューション）", "company": "IoT Solutions U", "industry": "IoT", "service": "IoT・センサソリューション開発", "strength": "技術力・ハードウェア", "gap": "営業・市場化", "client_industry": "製造業", "client_scale": "大企業", "value_chain": ["制作・開発・導入"], "asset": ["エンジニア"]},
    {"name": "瑞樹（リテール支援）", "company": "Retail Consulting V", "industry": "小売・リテール", "service": "小売業支援・営業支援", "strength": "業界知識・営業", "gap": "IT技術", "client_industry": "小売・飲食", "client_scale": "中小企業", "value_chain": ["営業・提案・クロージング"], "asset": ["コンサルタント"]},
    {"name": "舞（HRテック）", "company": "HR Tech W", "industry": "HRテック", "service": "人事管理システム・採用支援", "strength": "技術・HR知識", "gap": "営業", "client_industry": "全業種", "client_scale": "中堅企業", "value_chain": ["制作・開発・導入"], "asset": ["開発チーム"]},
    {"name": "陸（環境・サステナ）", "company": "Sustainability X", "industry": "環境・サステナビリティ", "service": "環境対応・ESG支援", "strength": "環境知識・戦略", "gap": "実装", "client_industry": "製造・エネルギー", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["コンサルタント"]},
    {"name": "愛莉（グロース支援）", "company": "Growth Hacking Y", "industry": "スタートアップ支援", "service": "グロースハッキング・スケール支援", "strength": "戦略・営業", "gap": "開発", "client_industry": "スタートアップ", "client_scale": "スタートアップ", "value_chain": ["営業・提案・クロージング"], "asset": ["コンサルタント"]},
    {"name": "勇輔（BtoB営業）", "company": "B2B Sales Z", "industry": "営業代理", "service": "BtoB営業代行・営業支援", "strength": "営業・営業戦略", "gap": "製品理解", "client_industry": "IT・SaaS", "client_scale": "スタートアップ", "value_chain": ["営業・提案・クロージング"], "asset": ["営業人材"]},
    {"name": "麗奈（カスタマーサクセス）", "company": "Customer Success AA", "industry": "SaaS", "service": "カスタマーサクセス・リテンション支援", "strength": "CS・顧客管理", "gap": "営業", "client_industry": "SaaS・IT", "client_scale": "スタートアップ", "value_chain": ["運用・保守・継続支援"], "asset": ["CSチーム"]},
    {"name": "健斗（メディア・コンテンツ）", "company": "Media Content AB", "industry": "メディア", "service": "オウンドメディア・コンテンツ制作", "strength": "コンテンツ・マーケティング", "gap": "営業", "client_industry": "全業種", "client_scale": "中小企業", "value_chain": ["認知・ブランディング"], "asset": ["コンテンツ制作チーム"]},
    {"name": "優季（データ分析）", "company": "Data Analytics AC", "industry": "データ分析", "service": "ビジネスデータ分析・ダッシュボード", "strength": "データ分析・可視化", "gap": "営業", "client_industry": "全業種", "client_scale": "大企業", "value_chain": ["経営・戦略・資金調達"], "asset": ["アナリスト"]},
    {"name": "拓郎（オンライン教育）", "company": "Online Education AD", "industry": "教育", "service": "オンラインコース・スキル育成", "strength": "教育コンテンツ・プラットフォーム", "gap": "営業・集客", "client_industry": "全業種", "client_scale": "スタートアップ", "value_chain": ["教育・研修・人材育成"], "asset": ["講師・インストラクター"]},
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
