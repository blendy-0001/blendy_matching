"""
Notion API との通信を担当するモジュール
"""
import requests
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from config import NOTION_API_KEY, MEMBERS_DB_ID, ACTIVITIES_DB_ID, MATCHING_HISTORY_DB_ID, MATCHING_RESULTS_DB_ID

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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
        try:
            res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.Timeout:
            logger.error("Notion API タイムアウト (get_all_members)")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Notion API 通信エラー (get_all_members): {e}")
            raise
        except Exception as e:
            logger.error(f"予期しないエラー (get_all_members): {e}")
            raise

        for page in data.get("results", []):
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
                "強み_キーワード":       _multi_select(props, "強み_キーワード"),
                "課題・足りないもの":    _text(props, "課題・足りないもの"),
                "課題_キーワード":       _multi_select(props, "課題_キーワード"),
                "保有アセット":          _multi_select(props, "保有アセット"),
                "事業フェーズ":          _select(props, "事業フェーズ"),
                "メール":                props.get("メール", {}).get("email", ""),
                "協業タイプ":            _select(props, "協業タイプ"),
                "LINE ID":               _text(props, "LINE ID"),
                "Facebook URL":          _url(props, "Facebook URL"),
            })
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return members


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_matched_pairs() -> set[frozenset]:
    """マッチング履歴から既にマッチング済みのペアセットを取得"""
    pairs = set()
    url = f"https://api.notion.com/v1/databases/{MATCHING_HISTORY_DB_ID}/query"
    payload = {}
    while True:
        try:
            res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            res.raise_for_status()
            data = res.json()
        except requests.exceptions.Timeout:
            logger.error("Notion API タイムアウト (get_matched_pairs)")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Notion API 通信エラー (get_matched_pairs): {e}")
            raise

        for page in data.get("results", []):
            props = page["properties"]
            a = _text(props, "メンバーA名")
            b = _text(props, "メンバーB名")
            if a and b:
                pairs.add(frozenset([a, b]))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return pairs


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_stats() -> dict:
    """ダッシュボード用の統計情報を取得"""
    try:
        # 総登録者数
        members_res = requests.post(
            f"https://api.notion.com/v1/databases/{MEMBERS_DB_ID}/query",
            headers=HEADERS,
            json={"filter": {"property": "ステータス", "select": {"equals": "アクティブ"}}},
            timeout=10
        )
        members_res.raise_for_status()
        members_data = members_res.json()

        total_members = len(members_data.get("results", []))
        has_more = members_data.get("has_more", False)
        if has_more:
            # 多い場合はページネーションで全件取得
            total_members = len(get_all_members())

        # 累計マッチング済み件数
        history_res = requests.post(
            f"https://api.notion.com/v1/databases/{MATCHING_HISTORY_DB_ID}/query",
            headers=HEADERS, json={},
            timeout=10
        )
        history_res.raise_for_status()
        history_data = history_res.json()

        total_matched = len(history_data.get("results", []))

        # マッチング可能件数（再マッチング除外後のペア数）
        n = total_members
        total_possible = n * (n - 1) // 2
        available = max(0, total_possible - total_matched)

        return {
            "総登録者数":         total_members,
            "マッチング可能件数": available,
            "累計マッチング済み": total_matched,
        }
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (get_stats)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (get_stats): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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
            "強み_キーワード":       {"multi_select": ms(data.get("強み_キーワード", []))},
            "課題・足りないもの":    {"rich_text": [{"text": {"content": data.get("課題・足りないもの", "")}}]},
            "課題_キーワード":       {"multi_select": ms(data.get("課題_キーワード", []))},
            "保有アセット":          {"multi_select": ms(data.get("保有アセット", []))},
            "事業フェーズ":          {"select": {"name": data["事業フェーズ"]}} if data.get("事業フェーズ") else {},
            "LINE ID":               {"rich_text": [{"text": {"content": data.get("LINE ID", "")}}]},
            "Facebook URL":          {"url": data.get("Facebook URL") or None},
            "ステータス":            {"select": {"name": "アクティブ"}},
        }
    }
    # 空の select プロパティを除去
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v}
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        return res.json().get("id", "")
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (create_member)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (create_member): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_activity(member_id: str, activity_data: dict) -> str:
    """
    activitiesテーブルに新規アクティビティを登録。ページIDを返す

    Args:
        member_id: members テーブルのレコード ID
        activity_data: {
            'アクティビティ名': str,
            'サービス内容': str,
            '強み_キーワード': list,
            '強み_詳細': str,
            '課題_キーワード': list,
            '課題_詳細': str,
            'バリューチェーン位置': list,
            '対象業界': str,
            '対象企業規模': str,
        }
    """
    if not ACTIVITIES_DB_ID:
        logger.warning("ACTIVITIES_DB_ID が設定されていません。アクティビティ保存をスキップします。")
        return ""

    url = "https://api.notion.com/v1/pages"

    def ms(values: list[str]) -> list[dict]:
        """multi_select用のリスト変換"""
        return [{"name": v} for v in (values or []) if v]

    payload = {
        "parent": {"database_id": ACTIVITIES_DB_ID},
        "properties": {
            "アクティビティ名": {"title": [{"text": {"content": activity_data.get("アクティビティ名", "")}}]},
            "サービス内容": {"rich_text": [{"text": {"content": activity_data.get("サービス内容", "")}}]},
            "強み_キーワード": {"multi_select": ms(activity_data.get("強み_キーワード", []))},
            "強み_詳細": {"rich_text": [{"text": {"content": activity_data.get("強み_詳細", "")}}]},
            "課題_キーワード": {"multi_select": ms(activity_data.get("課題_キーワード", []))},
            "課題_詳細": {"rich_text": [{"text": {"content": activity_data.get("課題_詳細", "")}}]},
            "バリューチェーン位置": {"multi_select": ms(activity_data.get("バリューチェーン位置", []))},
            "対象業界": {"rich_text": [{"text": {"content": activity_data.get("対象業界", "")}}]},
            "対象企業規模": {"select": {"name": activity_data["対象企業規模"]}} if activity_data.get("対象企業規模") else {},
            "member_id": {"relation": [{"id": member_id}]} if member_id else {},
        }
    }
    # 空のプロパティを除去
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v}

    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        result = res.json()
        logger.info(f"アクティビティ作成成功: {activity_data.get('アクティビティ名', 'Unknown')}")
        return result.get("id", "")
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (create_activity)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (create_activity): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_member_activities(member_id: str) -> list[dict]:
    """
    特定のメンバーの全アクティビティを取得

    Returns:
        アクティビティのリスト
    """
    if not ACTIVITIES_DB_ID:
        logger.warning("ACTIVITIES_DB_ID が設定されていません。空リストを返します。")
        return []

    url = f"https://api.notion.com/v1/databases/{ACTIVITIES_DB_ID}/query"
    payload = {
        "filter": {
            "property": "member_id",
            "relation": {"contains": member_id}
        },
        "page_size": 100
    }

    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()

        activities = []
        for page in data.get("results", []):
            props = page["properties"]
            activities.append({
                "id": page["id"],
                "アクティビティ名": _text(props, "アクティビティ名"),
                "サービス内容": _text(props, "サービス内容"),
                "強み_キーワード": _multi_select(props, "強み_キーワード"),
                "強み_詳細": _text(props, "強み_詳細"),
                "課題_キーワード": _multi_select(props, "課題_キーワード"),
                "課題_詳細": _text(props, "課題_詳細"),
                "バリューチェーン位置": _multi_select(props, "バリューチェーン位置"),
                "対象業界": _text(props, "対象業界"),
                "対象企業規模": _select(props, "対象企業規模"),
            })

        return activities
    except requests.exceptions.Timeout:
        logger.error(f"Notion API タイムアウト (get_member_activities): {member_id}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (get_member_activities): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        return res.json().get("id", "")
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (save_matching_result)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (save_matching_result): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (save_to_history)")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (save_to_history): {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def save_unmatched_member(session_name: str, member: dict) -> str:
    """マッチングされなかったメンバーをDBに保存。ページIDを返す"""
    from config import UNMATCHED_MEMBERS_DB_ID

    if not UNMATCHED_MEMBERS_DB_ID:
        # DB IDが設定されていない場合はスキップ
        logger.warning("UNMATCHED_MEMBERS_DB_ID が設定されていません")
        return ""

    logger.debug(f"マッチングされなかったメンバー保存開始: {member.get('名前', 'Unknown')}")

    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": UNMATCHED_MEMBERS_DB_ID},
        "properties": {
            "セッション名":           {"title": [{"text": {"content": session_name}}]},
            "メンバー名":             {"rich_text": [{"text": {"content": member.get("名前", "")}}]},
            "会社名":                 {"rich_text": [{"text": {"content": member.get("会社名", "")}}]},
            "業種カテゴリ":           {"select": {"name": member.get("業種カテゴリ", "")}} if member.get("業種カテゴリ") else {},
            "主力サービス":           {"rich_text": [{"text": {"content": member.get("主力サービス", "")}}]},
            "強み":                   {"rich_text": [{"text": {"content": member.get("強み", "")}}]},
            "課題・足りないもの":     {"rich_text": [{"text": {"content": member.get("課題・足りないもの", "")}}]},
            "記録日":                 {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        }
    }
    # 空の select プロパティを除去
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v}

    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        response_data = res.json()
        if "id" in response_data:
            logger.info(f"マッチングされなかったメンバー保存成功: {member.get('名前', 'Unknown')}")
            return response_data.get("id", "")
        else:
            logger.error(f"マッチングされなかったメンバー保存失敗: {response_data.get('message', 'Unknown error')}")
            return ""
    except requests.exceptions.Timeout:
        logger.error(f"Notion API タイムアウト (save_unmatched_member): {member.get('名前', 'Unknown')}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (save_unmatched_member): {e}")
        raise


# ── ヘルパー関数 ──────────────────────────────────
def _text(props: dict, key: str) -> str:
    try:
        items = props[key].get("rich_text") or props[key].get("title") or []
        text = "".join(i["plain_text"] for i in items)
        return " ".join(text.split())  # 前後のスペース削除 + 内部スペースを1つに正規化
    except KeyError:
        logger.debug(f"プロパティ '{key}' が見つかりません")
        return ""
    except (TypeError, AttributeError) as e:
        logger.debug(f"データ構造エラー ({key}): {type(e).__name__}")
        return ""
    except Exception as e:
        logger.warning(f"予期しないエラー (_text, {key}): {type(e).__name__}")
        return ""

def _select(props: dict, key: str) -> str:
    try:
        s = props[key].get("select")
        return s["name"] if s else ""
    except KeyError:
        logger.debug(f"プロパティ '{key}' が見つかりません")
        return ""
    except (TypeError, AttributeError) as e:
        logger.debug(f"データ構造エラー ({key}): {type(e).__name__}")
        return ""
    except Exception as e:
        logger.warning(f"予期しないエラー (_select, {key}): {type(e).__name__}")
        return ""

def _multi_select(props: dict, key: str) -> list[str]:
    try:
        return [o["name"] for o in props[key].get("multi_select", [])]
    except KeyError:
        logger.debug(f"プロパティ '{key}' が見つかりません")
        return []
    except (TypeError, AttributeError) as e:
        logger.debug(f"データ構造エラー ({key}): {type(e).__name__}")
        return []
    except Exception as e:
        logger.warning(f"予期しないエラー (_multi_select, {key}): {type(e).__name__}")
        return []

def _url(props: dict, key: str) -> str:
    try:
        return props[key].get("url") or ""
    except KeyError:
        logger.debug(f"プロパティ '{key}' が見つかりません")
        return ""
    except (TypeError, AttributeError) as e:
        logger.debug(f"データ構造エラー ({key}): {type(e).__name__}")
        return ""
    except Exception as e:
        logger.warning(f"予期しないエラー (_url, {key}): {type(e).__name__}")
        return ""
