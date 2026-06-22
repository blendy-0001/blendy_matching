"""
協業マッチングシステム 設定ファイル
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# ── Notion データベースID (作成用: /v1/pages で使用) ──────────────────────────
MEMBERS_DB_ID           = os.getenv("MEMBERS_DB_ID", "")  # 👥 メンバーリスト
ACTIVITIES_DB_ID        = os.getenv("ACTIVITIES_DB_ID", "")  # 🎯 事業アクティビティ（マルチアクティビティ対応）
MATCHING_HISTORY_DB_ID  = os.getenv("MATCHING_HISTORY_DB_ID", "")  # 🔗 マッチング履歴
MATCHING_RESULTS_DB_ID  = os.getenv("MATCHING_RESULTS_DB_ID", "")  # 📋 マッチング結果
UNMATCHED_MEMBERS_DB_ID = os.getenv("UNMATCHED_MEMBERS_DB_ID", "")  # 📊 マッチングされなかったメンバー

# ── Notion データソースID (クエリ用: /data_sources/{id}/query で使用) ──────────────────────────
MEMBERS_DATA_SOURCE_ID             = os.getenv("MEMBERS_DATA_SOURCE_ID", "")  # 👥 メンバーリスト
ACTIVITIES_DATA_SOURCE_ID          = os.getenv("ACTIVITIES_DATA_SOURCE_ID", "")  # 🎯 事業アクティビティ
MATCHING_HISTORY_DATA_SOURCE_ID    = os.getenv("MATCHING_HISTORY_DATA_SOURCE_ID", "")  # 🔗 マッチング履歴
MATCHING_RESULTS_DATA_SOURCE_ID    = os.getenv("MATCHING_RESULTS_DATA_SOURCE_ID", "")  # 📋 マッチング結果
UNMATCHED_MEMBERS_DATA_SOURCE_ID   = os.getenv("UNMATCHED_MEMBERS_DATA_SOURCE_ID", "")  # 📊 マッチングされなかったメンバー

# ── Phase 1: エラーログ＆分析結果（優先統合） ──────────────────────────
ERROR_LOGS_DB_ID                   = os.getenv("ERROR_LOGS_DB_ID", "")  # 🔴 エラーログ
ERROR_LOGS_DATA_SOURCE_ID          = os.getenv("ERROR_LOGS_DATA_SOURCE_ID", "")  # 🔴 エラーログ
ANALYSIS_RESULTS_DB_ID             = os.getenv("ANALYSIS_RESULTS_DB_ID", "")  # 📊 分析結果
ANALYSIS_RESULTS_DATA_SOURCE_ID    = os.getenv("ANALYSIS_RESULTS_DATA_SOURCE_ID", "")  # 📊 分析結果

# ── Phase 2-5: 今後の統合予定 ──────────────────────────
FOLLOWUP_DB_ID                     = os.getenv("FOLLOWUP_DB_ID", "")  # 📮 フォローアップ管理
FOLLOWUP_DATA_SOURCE_ID            = os.getenv("FOLLOWUP_DATA_SOURCE_ID", "")
EXCLUSION_RULES_DB_ID              = os.getenv("EXCLUSION_RULES_DB_ID", "")  # 🚫 除外ルール
EXCLUSION_RULES_DATA_SOURCE_ID     = os.getenv("EXCLUSION_RULES_DATA_SOURCE_ID", "")
EXECUTION_PARAMS_DB_ID             = os.getenv("EXECUTION_PARAMS_DB_ID", "")  # ⚙️ 実行パラメータ
EXECUTION_PARAMS_DATA_SOURCE_ID    = os.getenv("EXECUTION_PARAMS_DATA_SOURCE_ID", "")
SCORING_RULES_DB_ID                = os.getenv("SCORING_RULES_DB_ID", "")  # 📏 スコアリングルール
SCORING_RULES_DATA_SOURCE_ID       = os.getenv("SCORING_RULES_DATA_SOURCE_ID", "")
CAMPAIGN_MGMT_DB_ID                = os.getenv("CAMPAIGN_MGMT_DB_ID", "")  # 📢 キャンペーン管理
CAMPAIGN_MGMT_DATA_SOURCE_ID       = os.getenv("CAMPAIGN_MGMT_DATA_SOURCE_ID", "")
SUCCESS_STORIES_DB_ID              = os.getenv("SUCCESS_STORIES_DB_ID", "")  # ⭐ 成功事例
SUCCESS_STORIES_DATA_SOURCE_ID     = os.getenv("SUCCESS_STORIES_DATA_SOURCE_ID", "")

# ── マッチング設定 ────────────────────────────────
MIN_SCORE = 45           # 高品質マッチングのみ（ルール版用）
MAX_MATCHES_PER_RUN = 30  # 1回の実行で生成する最大ペア数（ユーザーが残り3件を手動調整）

# ── スコアリング配点 ─────────────────────────────
SCORE_WEIGHTS = {
    "エンドクライアント一致度":    30,  # 同じクライアント層か
    "バリューチェーン接続性":       25,  # 前後工程でつながるか
    "市場ソリューションフィット":   25,  # 技術×市場の補完か
    "事業拡張ポテンシャル":         20,  # 協業で事業が広がるか
}

# ── 協業タイプ定義 ───────────────────────────────
COLLABORATION_TYPES = {
    "A": "バリューチェーン型：同じクライアントへの前後工程",
    "B": "市場参入型：ソリューション×市場（顧客基盤）",
    "C": "バンドル強化型：同じクライアントへの並列補完",
    "D": "OEM・裏方型：フロント×実務の役割分担",
    "E": "相互紹介型：クライアントを紹介し合う",
    "F": "共同開発型：一緒に新サービスを作る",
    "G": "リソース補完型：キャパシティ・人材のシェア",
}

# ── 業界キーワード辞書（精度90%向上用 - Priority 2） ─────────
INDUSTRY_KEYWORDS = {
    "ソリューション系": [
        "開発", "技術", "システム", "API", "デザイン", "製造",
        "クラウド", "AI", "機械学習", "データ分析", "セキュリティ",
        "IoT", "ブロックチェーン", "Web3", "RPA", "自動化",
        "インフラ", "データベース", "アーキテクチャ", "最適化",
        "モバイル", "バックエンド", "フロントエンド", "UX", "エンジニアリング",
        "テック", "ソフトウェア", "ハードウェア", "通信", "ネットワーク",
    ],
    "マーケット系": [
        "営業", "マーケティング", "営業支援", "ネットワーク", "顧客基盤",
        "カスタマーサクセス", "営業代理", "パートナー", "流通",
        "リサーチ", "ブランド", "PR", "イベント", "展示会",
        "セールス", "営業開発", "BDR", "営業コンサル", "営業戦略",
        "市場開拓", "販路拡大", "顧客開拓", "リード生成", "見込み客育成",
    ],
    "業界別": [
        "医療", "金融", "不動産", "小売", "製造", "流通", "教育",
        "SaaS", "EdTech", "FinTech", "HealthTech", "LegalTech",
        "農業", "建設", "運輸", "物流", "エネルギー", "通信",
        "スタートアップ", "ベンチャー", "大企業", "中小企業", "グローバル",
    ],
}
