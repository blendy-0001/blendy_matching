"""
協業マッチングシステム 設定ファイル
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# ── Notion データベースID ──────────────────────────
MEMBERS_DB_ID           = os.getenv("MEMBERS_DB_ID", "517b9ae4-8e9d-496d-b581-927bde2af2fe")  # 👥 メンバーリスト
MATCHING_HISTORY_DB_ID  = os.getenv("MATCHING_HISTORY_DB_ID", "f650ca34-90b9-49e7-908e-240394dd47ed")  # 🔗 マッチング履歴
MATCHING_RESULTS_DB_ID  = os.getenv("MATCHING_RESULTS_DB_ID", "968cbe70-f0be-4f7c-8015-e275655e880e")  # 📋 マッチング結果
UNMATCHED_MEMBERS_DB_ID = os.getenv("UNMATCHED_MEMBERS_DB_ID", "")  # 📊 マッチングされなかったメンバー

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
