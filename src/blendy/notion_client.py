"""
Notion API との通信を担当するモジュール
"""
import requests
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import (
    NOTION_API_KEY,
    MEMBERS_DB_ID,
    ACTIVITIES_DB_ID,
    MATCHING_HISTORY_DB_ID,
    MATCHING_RESULTS_DB_ID,
    UNMATCHED_MEMBERS_DB_ID,
    MEMBERS_DATA_SOURCE_ID,
    ACTIVITIES_DATA_SOURCE_ID,
    MATCHING_HISTORY_DATA_SOURCE_ID,
    MATCHING_RESULTS_DATA_SOURCE_ID,
    UNMATCHED_MEMBERS_DATA_SOURCE_ID,
    ERROR_LOGS_DB_ID,
    ERROR_LOGS_DATA_SOURCE_ID,
    ANALYSIS_RESULTS_DB_ID,
    ANALYSIS_RESULTS_DATA_SOURCE_ID,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_all_members() -> list[dict]:
    """メンバーリストDBからアクティブなメンバーを全員取得"""
    members = []
    url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DATA_SOURCE_ID}/query"
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
            member = {
                "id":              page["id"],
                "名前":            _text(props, "名前"),
                "会社名":          _text(props, "会社名"),
                "業種カテゴリ":    _select(props, "業種カテゴリ"),
                "業種詳細":        _text(props, "業種詳細"),
                "事業フェーズ":    _select(props, "事業フェーズ"),
                "LINE ID":         _text(props, "LINE ID"),
                "Facebook URL":    _url(props, "Facebook URL"),
            }

            # アクティビティ数と最初のアクティビティを取得（存在する場合）
            if "アクティビティ数" in props:
                activity_count = props["アクティビティ数"].get("number")
                if activity_count is not None:
                    member["アクティビティ数"] = activity_count
            if "最初のアクティビティ" in props:
                first_activity = _text(props, "最初のアクティビティ")
                if first_activity:
                    member["最初のアクティビティ"] = first_activity

            members.append(member)
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return members


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_matched_pairs() -> set[frozenset]:
    """マッチング履歴から既にマッチング済みのペアセットを取得"""
    pairs = set()
    url = f"https://api.notion.com/v1/data_sources/{MATCHING_HISTORY_DATA_SOURCE_ID}/query"
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
        # Check if data source IDs are properly configured
        if not MEMBERS_DATA_SOURCE_ID:
            logger.error("[CONFIG ERROR] MEMBERS_DATA_SOURCE_ID is not set in config.py")
            raise ValueError("MEMBERS_DATA_SOURCE_ID is not configured")

        logger.info(f"[DEBUG] Attempting to query MEMBERS with ID: {MEMBERS_DATA_SOURCE_ID}")

        # 総登録者数
        members_url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DATA_SOURCE_ID}/query"
        logger.debug(f"[DEBUG] Using endpoint: {members_url}")

        members_res = requests.post(
            members_url,
            headers=HEADERS,
            json={"filter": {"property": "ステータス", "select": {"equals": "アクティブ"}}},
            timeout=10
        )

        if members_res.status_code == 404:
            logger.error(f"[CONFIG ERROR] MEMBERS_DATA_SOURCE_ID '{MEMBERS_DATA_SOURCE_ID}' not found in Notion.")

        members_res.raise_for_status()
        members_data = members_res.json()

        total_members = len(members_data.get("results", []))
        has_more = members_data.get("has_more", False)
        if has_more:
            # 多い場合はページネーションで全件取得
            total_members = len(get_all_members())

        # 累計マッチング済み件数
        history_res = requests.post(
            f"https://api.notion.com/v1/data_sources/{MATCHING_HISTORY_DATA_SOURCE_ID}/query",
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

    payload = {
        "parent": {"database_id": MEMBERS_DB_ID},
        "properties": {
            "名前": {"title": [{"text": {"content": data.get("名前", "")}}]},
            "会社名": {"rich_text": [{"text": {"content": data.get("会社名", "")}}]},
            "業種カテゴリ": {"select": {"name": data.get("業種カテゴリ")}} if data.get("業種カテゴリ") else {},
            "業種詳細": {"rich_text": [{"text": {"content": data.get("業種詳細", "")}}]},
            "事業フェーズ": {"select": {"name": data.get("事業フェーズ")}} if data.get("事業フェーズ") else {},
            "ステータス": {"select": {"name": "アクティブ"}},
        }
    }
    # オプションフィールド: LINE ID, Facebook URL があれば追加
    if data.get("LINE ID"):
        payload["properties"]["LINE ID"] = {"rich_text": [{"text": {"content": data["LINE ID"]}}]}
    if data.get("Facebook URL"):
        payload["properties"]["Facebook URL"] = {"url": data["Facebook URL"]}

    # アクティビティ数を保存
    logger.debug(f"[DEBUG] data.get('アクティビティ数')={data.get('アクティビティ数')}, type={type(data.get('アクティビティ数'))}")
    if data.get("アクティビティ数"):
        payload["properties"]["アクティビティ数"] = {"number": data.get("アクティビティ数")}
        logger.info(f"[DEBUG] アクティビティ数を追加: {data.get('アクティビティ数')}")

    # 最初のアクティビティを保存
    logger.debug(f"[DEBUG] data.get('最初のアクティビティ')={data.get('最初のアクティビティ')}")
    if data.get("最初のアクティビティ"):
        payload["properties"]["最初のアクティビティ"] = {"rich_text": [{"text": {"content": data.get("最初のアクティビティ", "")}}]}
        logger.info(f"[DEBUG] 最初のアクティビティを追加: {data.get('最初のアクティビティ')}")

    # フィルタリング前のプロパティキー
    logger.debug(f"[DEBUG] フィルタリング前のキー: {list(payload['properties'].keys())}")

    # 空の select プロパティを除去
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v}

    # フィルタリング後のプロパティキー
    logger.debug(f"[DEBUG] フィルタリング後のキー: {list(payload['properties'].keys())}")

    # デバッグログ - 詳細な情報を記録
    logger.info(f"[CREATE_MEMBER] 入力: アクティビティ数={data.get('アクティビティ数')}, 最初のアクティビティ={data.get('最初のアクティビティ')}")
    logger.debug(f"[CREATE_MEMBER] Payload properties keys: {list(payload['properties'].keys())}")
    if 'アクティビティ数' in payload['properties']:
        logger.info(f"[CREATE_MEMBER] ✓ アクティビティ数がペイロードに含まれている: {payload['properties']['アクティビティ数']}")
    else:
        logger.warning(f"[CREATE_MEMBER] ✗ アクティビティ数がペイロードに含まれていない")
    if '最初のアクティビティ' in payload['properties']:
        logger.info(f"[CREATE_MEMBER] ✓ 最初のアクティビティがペイロードに含まれている")
    else:
        logger.warning(f"[CREATE_MEMBER] ✗ 最初のアクティビティがペイロードに含まれていない")

    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        result = res.json()
        page_id = result.get("id", "")
        logger.info(f"[CREATE_MEMBER OK] page_id={page_id}")
        return page_id
    except requests.exceptions.Timeout:
        logger.error("Notion API タイムアウト (create_member)")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError (create_member): status={e.response.status_code}, body={e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (create_member): {e}")
        raise
    except Exception as e:
        logger.error(f"予期しないエラー (create_member): {e}")
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
            "メンバー": {"relation": [{"id": member_id}]} if member_id else {},
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
    if not ACTIVITIES_DATA_SOURCE_ID:
        logger.warning("ACTIVITIES_DATA_SOURCE_ID が設定されていません。空リストを返します。")
        return []

    url = f"https://api.notion.com/v1/data_sources/{ACTIVITIES_DATA_SOURCE_ID}/query"
    payload = {
        "filter": {
            "property": "メンバー",
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
            "セッション名":   {"title": [{"text": {"content": session_name}}]},
            "メンバー名":     {"rich_text": [{"text": {"content": member.get("名前", "")}}]},
            "会社名":         {"rich_text": [{"text": {"content": member.get("会社名", "")}}]},
            "業種カテゴリ":   {"select": {"name": member.get("業種カテゴリ", "")}} if member.get("業種カテゴリ") else {},
            "業種詳細":       {"rich_text": [{"text": {"content": member.get("業種詳細", "")}}]},
            "事業フェーズ":   {"select": {"name": member.get("事業フェーズ", "")}} if member.get("事業フェーズ") else {},
            "記録日":         {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
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


# ── Activities DB 関連の関数 ─────────────────────

_activities_cache = {}  # メンバー名 → Activities リストのメモリキャッシュ


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_activities_for_member(member_id: str, use_cache: bool = True) -> list[dict]:
    """
    ACTIVITIES_DB から指定メンバーのすべての activities を取得

    Args:
        member_id: メンバーの Notion ページ ID
        use_cache: メモリキャッシュを使用するか

    Returns:
        activities のリスト。各要素は活動プロフィール dict
    """
    # キャッシュチェック
    if use_cache and member_id in _activities_cache:
        return _activities_cache[member_id]

    activities = []
    url = f"https://api.notion.com/v1/data_sources/{ACTIVITIES_DATA_SOURCE_ID}/query"
    payload = {
        "filter": {
            "property": "メンバー",
            "relation": {
                "contains": member_id
            }
        }
    }

    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.Timeout:
        logger.error(f"Notion API タイムアウト (get_activities_for_member: {member_id})")
        return []  # timeout 時は空リスト返却で scoring 続行
    except requests.exceptions.RequestException as e:
        logger.error(f"Notion API 通信エラー (get_activities_for_member: {member_id}): {e}")
        return []  # 通信エラー時も空リスト返却で scoring 続行
    except Exception as e:
        logger.error(f"予期しないエラー (get_activities_for_member): {e}")
        return []

    for page in data.get("results", []):
        activity = _extract_activity(page["properties"])
        activities.append(activity)

    # キャッシュに保存
    _activities_cache[member_id] = activities
    return activities


def _extract_activity(props: dict) -> dict:
    """
    Activities row から各プロパティを抽出して dict に変換

    Returns:
        活動プロフィール dict
    """
    return {
        "アクティビティ名": _text(props, "アクティビティ名"),
        "サービス内容": _text(props, "サービス内容"),
        "対象業界": _text(props, "対象業界"),
        "対象企業規模": _select(props, "対象企業規模"),
        "強み": _multi_select(props, "強み_キーワード"),
        "強み_詳細": _text(props, "強み_詳細"),
        "課題": _multi_select(props, "課題_キーワード"),
        "課題_詳細": _text(props, "課題_詳細"),
        "ポジション": _multi_select(props, "バリューチェーン位置"),
    }


def clear_activities_cache():
    """メモリキャッシュをクリア（テスト用）"""
    global _activities_cache
    _activities_cache.clear()


# ────────────────────────────────────────────────────────
# Phase 1: エラーログ＆分析結果の自動保存機能
# ────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def save_error_log(
    error_type: str,
    error_message: str,
    analysis: str,
    affected_member: str = "",
    response_status: str = "未対応",
) -> bool:
    """
    エラーを Error Logs DB に自動ロギング

    Args:
        error_type: エラータイプ（"データ不整合", "API通信エラー", "バリデーションエラー", "スコアリング異常", "その他"）
        error_message: エラーメッセージ（ユーザーへの汎用メッセージ）
        analysis: 原因分析（技術者向けの詳細分析）
        affected_member: 影響を受けたメンバー名（オプション）
        response_status: 対応状況デフォルト "未対応"

    Returns:
        bool: 成功時 True、失敗時 False
    """
    try:
        # ページ作成用 payload
        payload = {
            "parent": {"database_id": ERROR_LOGS_DB_ID},
            "properties": {
                "ログID": {
                    "title": [
                        {
                            "text": {
                                "content": f"[{error_type}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                },
                "エラータイプ": {
                    "select": {"name": error_type}
                },
                "エラー発生日時": {
                    "date": {"start": datetime.now().isoformat()}
                },
                "原因分析": {
                    "rich_text": [
                        {
                            "text": {"content": analysis}
                        }
                    ]
                },
                "対応内容": {
                    "rich_text": [
                        {
                            "text": {"content": error_message}
                        }
                    ]
                },
                "対応状況": {
                    "select": {"name": response_status}
                },
            },
        }

        # オプションフィールドの追加
        if affected_member:
            payload["properties"]["関連メンバー"] = {
                "rich_text": [{"text": {"content": affected_member}}]
            }

        url = "https://api.notion.com/v1/pages"
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()

        logger.info(f"✅ エラーログ保存完了: {error_type}")
        return True

    except requests.exceptions.Timeout:
        logger.error(f"❌ Notion API タイムアウト (save_error_log): {error_type}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Notion API エラー (save_error_log): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ エラーログ保存失敗: {e}")
        return False


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def save_matching_analysis(
    session_name: str,
    matching_results: list[dict],
    statistics: dict,
) -> bool:
    """
    マッチング分析結果を Analysis Results DB に自動保存

    Args:
        session_name: セッション名（例："20260531_matching_001"）
        matching_results: マッチング結果のリスト（各要素が {"メンバーA名": "...", "メンバーB名": "...", "スコア": ...} 形式）
        statistics: 統計情報辞書
            - "total_matched": マッチングされたペア数
            - "total_members": マッチング対象メンバー数
            - "avg_score": 平均スコア
            - "max_score": 最高スコア
            - "score_distribution": {"45-60": 3, "60-80": 5, "80-100": 2} 等

    Returns:
        bool: 成功時 True、失敗時 False
    """
    try:
        # スコア分布を計算
        score_dist = statistics.get("score_distribution", {})
        score_45_60 = score_dist.get("45-60", 0)
        score_60_80 = score_dist.get("60-80", 0)
        score_80_100 = score_dist.get("80-100", 0)

        # マッチング成功率を計算（成功 = マッチングされたペア数 > 0）
        total_members = statistics.get("total_members", 1)
        total_matched = statistics.get("total_matched", 0)
        success_rate = (total_matched / max(total_members, 1)) * 100

        # 平均スコア
        avg_score = statistics.get("avg_score", 0)

        # 分析対象期間（今日）
        today = datetime.now().isoformat()

        # ページ作成用 payload
        payload = {
            "parent": {"database_id": ANALYSIS_RESULTS_DB_ID},
            "properties": {
                "分析レポートID": {
                    "title": [
                        {
                            "text": {
                                "content": f"{session_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                            }
                        }
                    ]
                },
                "マッチング成功率": {
                    "number": round(success_rate, 2)
                },
                "スコア分布_45-60点": {
                    "number": score_45_60
                },
                "スコア分布_60-80点": {
                    "number": score_60_80
                },
                "スコア分布_80-100点": {
                    "number": score_80_100
                },
                "平均スコア": {
                    "number": round(avg_score, 2)
                },
                "作成日": {
                    "date": {"start": today}
                },
                "主な失敗要因": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"処理対象メンバー数: {total_members}, マッチング成功ペア数: {total_matched}"
                            }
                        }
                    ]
                },
            },
        }

        url = "https://api.notion.com/v1/pages"
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        res.raise_for_status()

        logger.info(f"✅ マッチング分析結果保存完了: {session_name}")
        return True

    except requests.exceptions.Timeout:
        logger.error(f"❌ Notion API タイムアウト (save_matching_analysis): {session_name}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Notion API エラー (save_matching_analysis): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ マッチング分析保存失敗: {e}")
        return False
