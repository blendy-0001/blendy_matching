"""
Notion API との通信を担当するモジュール
"""
import requests
from datetime import datetime
from config import NOTION_API_KEY, MEMBERS_DB_ID, MATCHING_HISTORY_DB_ID, MATCHING_RESULTS_DB_ID

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_all_members() -> list[dict]:
    """メンバーリストDBからアクティブなメンバーを全員取得"""
    members = []
    url = f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}/query"
    payload = {
        "filter": {
            "property": "ステータス",
            "select": {"equals": "アクティブ"}
        }
    }
    while True:
        res = requests.post(url, headers=HEADERS, json=payload).json()
        for page in res.get("results", []):
            props = page["properties"]
            members.append({
                "id":                    page["id"],
                "名前":                  _text(props, "名前"),
                "会社名":                _text(props, "会社名"),
                "業種カテゴリ":          _select(props, "業種カテゴリ"),
                "業種詳細":              _text(props, "業種詳細"),
                "主力サービス":          _text(props, "主力サービス"),
                "エンドクライアント業界": _text(props, "エンドクライアント業界"),
                "エンドクライアント規模": _select(props, "エンドクライアント規模"),
                "クライアントの課題":    _text(props, "クライアントの課題"),
                "バリューチェーン位置":  _multi_select(props, "バリューチェーン位置"),
                "強み":                  _text(props, "強み"),
                "課題・足りないもの":    _text(props, "課題・足りないもの"),
                "保有アセット":          _multi_select(props, "保有アセット"),
                "事業フェーズ":          _select(props, "事業フェーズ"),
                "LINE ID":               _text(props, "LINE ID"),
                "Facebook URL":          _url(props, "Facebook URL"),
            })
        if not res.get("has_more"):
            break
        payload["start_cursor"] = res["next_cursor"]
    return members


def get_matched_pairs() -> set[frozenset]:
    """マッチング履歴から既にマッチング済みのペアセットを取得"""
    pairs = set()
    url = f"https://api.notion.com/v1/databases/{MATCHING_HISTORY_DB_ID}/query"
    payload = {}
    while True:
        res = requests.post(url, headers=HEADERS, json=payload).json()
        for page in res.get("results", []):
            props = page["properties"]
            a = _text(props, "メンバーA名")
            b = _text(props, "メンバーB名")
            if a and b:
                pairs.add(frozenset([a, b]))
        if not res.get("has_more"):
            break
        payload["start_cursor"] = res["next_cursor"]
    return pairs


def get_stats() -> dict:
    """ダッシュボード用の統計情報を取得"""
    # 総登録者数
    members_res = requests.post(
        f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}/query",
        headers=HEADERS,
        json={"filter": {"property": "ステータス", "select": {"equals": "アクティブ"}}}
    ).json()
    total_members = len(members_res.get("results", []))
    has_more = members_res.get("has_more", False)
    if has_more:
        # 多い場合はページネーションで全件取得
        total_members = len(get_all_members())

    # 累計マッチング済み件数
    history_res = requests.post(
        f"https://api.notion.com/v1/databases/{MATCHING_HISTORY_DB_ID}/query",
        headers=HEADERS, json={}
    ).json()
    total_matched = len(history_res.get("results", []))

    # マッチング可能件数（再マッチング除外後のペア数）
    n = total_members
    total_possible = n * (n - 1) // 2
    available = max(0, total_possible - total_matched)

    return {
        "総登録者数":         total_members,
        "マッチング可能件数": available,
        "累計マッチング済み": total_matched,
    }


def create_member(data: dict) -> str:
    """メンバーリストDBに新規メンバーを登録。ページIDを返す"""
    url = "https://api.notion.com/v1/pages"

    def ms(values: list[str]) -> list[dict]:
        return [{"name": v} for v in values if v]

    payload = {
        "parent": {"database_id": MEMBERS_DB_ID},
        "properties": {
            "名前":                  {"title": [{"text": {"content": data.get("名前", "")}}]},
            "会社名":                {"rich_text": [{"text": {"content": data.get("会社名", "")}}]},
            "業種カテゴリ":          {"select": {"name": data["業種カテゴリ"]}} if data.get("業種カテゴリ") else {},
            "業種詳細":              {"rich_text": [{"text": {"content": data.get("業種詳細", "")}}]},
            "主力サービス":          {"rich_text": [{"text": {"content": data.get("主力サービス", "")}}]},
            "エンドクライアント業界": {"rich_text": [{"text": {"content": data.get("エンドクライアント業界", "")}}]},
            "エンドクライアント規模": {"select": {"name": data["エンドクライアント規模"]}} if data.get("エンドクライアント規模") else {},
            "クライアントの課題":    {"rich_text": [{"text": {"content": data.get("クライアントの課題", "")}}]},
            "バリューチェーン位置":  {"multi_select": ms(data.get("バリューチェーン位置", []))},
            "強み":                  {"rich_text": [{"text": {"content": data.get("強み", "")}}]},
            "課題・足りないもの":    {"rich_text": [{"text": {"content": data.get("課題・足りないもの", "")}}]},
            "保有アセット":          {"multi_select": ms(data.get("保有アセット", []))},
            "事業フェーズ":          {"select": {"name": data["事業フェーズ"]}} if data.get("事業フェーズ") else {},
            "LINE ID":               {"rich_text": [{"text": {"content": data.get("LINE ID", "")}}]},
            "Facebook URL":          {"url": data.get("Facebook URL") or None},
            "ステータス":            {"select": {"name": "アクティブ"}},
        }
    }
    # 空の select プロパティを除去
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v}
    res = requests.post(url, headers=HEADERS, json=payload).json()
    return res.get("id", "")


def save_matching_result(session_name: str, match: dict) -> str:
    """マッチング結果DBに1ペアを保存。ページIDを返す"""
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": MATCHING_RESULTS_DB_ID},
        "properties": {
            "セッション名":             {"title": [{"text": {"content": session_name}}]},
            "メンバーA名":              {"rich_text": [{"text": {"content": match["メンバーA名"]}}]},
            "メンバーB名":              {"rich_text": [{"text": {"content": match["メンバーB名"]}}]},
            "協業タイプ":               {"select": {"name": match["協業タイプ"]}},
            "スコア":                   {"number": match["スコア"]},
            "エンドクライアント一致度": {"number": match["内訳"]["エンドクライアント一致度"]},
            "バリューチェーン接続性":   {"number": match["内訳"]["バリューチェーン接続性"]},
            "市場ソリューションフィット": {"number": match["内訳"]["市場ソリューションフィット"]},
            "事業拡張ポテンシャル":     {"number": match["内訳"]["事業拡張ポテンシャル"]},
            "マッチング理由":           {"rich_text": [{"text": {"content": match["マッチング理由"]}}]},
            "紹介文":                   {"rich_text": [{"text": {"content": match["紹介文"]}}]},
            "実施日":                   {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "ステータス":               {"select": {"name": "生成済み"}},
        }
    }
    res = requests.post(url, headers=HEADERS, json=payload).json()
    return res.get("id", "")


def save_to_history(match: dict):
    """マッチング履歴DBにペアを記録（再マッチング防止用）"""
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": MATCHING_HISTORY_DB_ID},
        "properties": {
            "メンバーA名":    {"title": [{"text": {"content": match["メンバーA名"]}}]},
            "メンバーB名":    {"rich_text": [{"text": {"content": match["メンバーB名"]}}]},
            "協業タイプ":     {"select": {"name": match["協業タイプ"]}},
            "スコア":         {"number": match["スコア"]},
            "マッチング実施日": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        }
    }
    requests.post(url, headers=HEADERS, json=payload)


# ── ヘルパー関数 ──────────────────────────────────
def _text(props: dict, key: str) -> str:
    try:
        items = props[key].get("rich_text") or props[key].get("title") or []
        return "".join(i["plain_text"] for i in items)
    except Exception:
        return ""

def _select(props: dict, key: str) -> str:
    try:
        s = props[key].get("select")
        return s["name"] if s else ""
    except Exception:
        return ""

def _multi_select(props: dict, key: str) -> list[str]:
    try:
        return [o["name"] for o in props[key].get("multi_select", [])]
    except Exception:
        return []

def _url(props: dict, key: str) -> str:
    try:
        return props[key].get("url") or ""
    except Exception:
        return ""
