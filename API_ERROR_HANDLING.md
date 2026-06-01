# API エラーハンドリングガイド

**バージョン**: 1.0.0  
**最終更新**: 2026-05-25  
**対象**: Blendy Matching API クライアント

---

## 概要

このドキュメントは、Blendy Matching API のエラーレスポンスと対応方法をクライアント開発者向けに説明しています。

API は標準的な HTTP ステータスコードを使用し、各エラーは詳細な情報をレスポンスボディに含めます。

---

## HTTP ステータスコード一覧

| ステータスコード | 説明 | 原因 |
|---|---|---|
| 200 | OK | リクエスト成功 |
| 422 | Unprocessable Content | バリデーションエラー（必須フィールド欠落など） |
| 403 | Forbidden | API キー認証失敗（本番環境） |
| 401 | Unauthorized | 認証情報が無効または期限切れ |
| 500 | Internal Server Error | サーバー内部エラー |

---

## エラーレスポンス形式

### 標準エラーレスポンス（422, 403, 401, 500）

```json
{
  "detail": "エラーの詳細説明"
}
```

### バリデーションエラーレスポンス（422）

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "x-api-key"],
      "msg": "field required"
    }
  ]
}
```

---

## エンドポイント別エラー仕様

### 1️⃣ GET /api/stats

**認証**: 不要  
**説明**: ダッシュボード統計情報取得

**可能なレスポンス:**

| ステータス | 説明 | 例 |
|---|---|---|
| 200 | 統計情報取得成功 | `{"success": true, "stats": {...}, "running": false, "progress": ""}` |
| 500 | 統計情報取得失敗 | `{"detail": "Failed to fetch statistics from Notion"}` |

**クライアント実装例:**

```python
import requests

response = requests.get("http://localhost:8000/api/stats")

if response.status_code == 200:
    data = response.json()
    stats = data["stats"]
    print(f"総登録者数: {stats.get('総登録者数')}")
elif response.status_code == 500:
    error = response.json()
    print(f"エラー: {error['detail']}")
```

---

### 2️⃣ POST /api/register

**認証**: 不要  
**説明**: 新規メンバー登録

**必須フィールド:**
- `名前`: 企業名または代表者名

**可能なレスポンス:**

| ステータス | 説明 | 例 |
|---|---|---|
| 200 | 登録成功 | `{"success": true, "page_id": "12345abc..."}` |
| 422 | 必須フィールド欠落 | `{"detail": [{"type": "missing", "loc": ["form", "名前"]}]}` |
| 500 | 登録処理エラー | `{"detail": "Failed to create member in Notion"}` |

**422 エラーの例: 「名前」が未入力**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["form", "名前"],
      "msg": "field required"
    }
  ]
}
```

**クライアント実装例:**

```python
import requests

data = {
    "名前": "ABC株式会社",
    "会社名": "ABC Corp",
    "業種カテゴリ": "IT",
}

response = requests.post(
    "http://localhost:8000/api/register",
    data=data
)

if response.status_code == 200:
    result = response.json()
    print(f"登録完了: {result['page_id']}")
elif response.status_code == 422:
    errors = response.json()["detail"]
    for error in errors:
        print(f"エラー: {error['loc']} - {error['msg']}")
elif response.status_code == 500:
    error = response.json()
    print(f"サーバーエラー: {error['detail']}")
```

---

### 3️⃣ POST /api/run-matching

**認証**: 本番環境で必須（X-API-Key ヘッダー）  
**説明**: AI マッチング処理開始

**ヘッダー:**
```
X-API-Key: {your-api-key}
```

**可能なレスポンス:**

| ステータス | 説明 | 例 | 対応方法 |
|---|---|---|---|
| 200 | マッチング開始成功 | `{"success": true, "message": "マッチングを開始しました"}` | `/api/results` で進捗確認 |
| 422 | X-API-Key ヘッダー欠落 | `{"detail": [{"type": "missing", "loc": ["header", "x-api-key"]}]}` | ヘッダーにキーを追加 |
| 403 | API キー無効 | `{"detail": "Invalid or missing API key"}` | API キーを確認 |
| 500 | マッチング処理エラー | `{"detail": "..."}` | サーバーログを確認 |

**422 エラー: X-API-Key ヘッダーが見つかりません**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "x-api-key"],
      "msg": "field required"
    }
  ]
}
```

**対応**: リクエストヘッダーに `X-API-Key` を追加してください。

```bash
curl -X POST http://localhost:8000/api/run-matching \
  -H "X-API-Key: your-api-key-here"
```

**403 エラー: 無効な API キー**

```json
{
  "detail": "Invalid or missing API key"
}
```

**対応**: Render 管理画面で API キーを確認し、正しい値を送信してください。

**クライアント実装例:**

```python
import requests
import time

API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8000"

# マッチング開始
response = requests.post(
    f"{BASE_URL}/api/run-matching",
    headers={"X-API-Key": API_KEY},
    params={"max_matches": 15}
)

if response.status_code == 200:
    print("✅ マッチング開始成功")
    
    # 結果ポーリング
    while True:
        result_response = requests.get(f"{BASE_URL}/api/results")
        result_data = result_response.json()
        
        if not result_data["running"]:
            print(f"✅ マッチング完了")
            print(f"マッチペア数: {len(result_data['results']['matched'])}")
            break
        
        print(f"⏳ {result_data['progress']}")
        time.sleep(5)
        
elif response.status_code == 422:
    print("❌ X-API-Key ヘッダーが見つかりません")
elif response.status_code == 403:
    print("❌ API キー認証失敗")
```

---

### 4️⃣ GET /api/results

**認証**: 不要  
**説明**: マッチング結果取得

**可能なレスポンス:**

| ステータス | 説明 | 用途 |
|---|---|---|
| 200 | 結果取得成功 | マッチング実行中の進捗確認、完了後の結果取得 |
| 500 | 結果取得失敗 | エラーハンドリング |

**実行中のレスポンス例:**

```json
{
  "success": true,
  "running": true,
  "progress": "AIがマッチングを分析中...（目標: 15組、しばらくお待ちください）",
  "results": null
}
```

**完了時のレスポンス例:**

```json
{
  "success": true,
  "running": false,
  "progress": "✅ 12組のマッチングが完了しました！",
  "results": {
    "matched": [
      {
        "メンバーA名": "ABC株式会社",
        "メンバーB名": "XYZ株式会社",
        "スコア": 87.5,
        "協業タイプ": "A",
        "マッチング理由": "同じエンドクライアント層をターゲット",
        "紹介文": "デジタルマーケティング領域での相性抜群..."
      }
    ],
    "unmatched": [
      {
        "名前": "PQR株式会社",
        "理由": "マッチングされなかった（スコア不足）"
      }
    ]
  }
}
```

**クライアント実装例:**

```python
import requests

def poll_matching_results(max_wait_seconds=300):
    """マッチング完了までポーリング"""
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            print("⏱️ タイムアウト: マッチング処理が長時間かかっています")
            break
        
        response = requests.get("http://localhost:8000/api/results")
        
        if response.status_code != 200:
            print(f"❌ エラー: {response.json()['detail']}")
            break
        
        data = response.json()
        
        if data["running"]:
            print(f"⏳ {data['progress']}")
            time.sleep(2)
        else:
            print(f"✅ {data['progress']}")
            results = data.get("results", {})
            return results

# 使用
results = poll_matching_results()
if results:
    for match in results.get("matched", []):
        print(f"{match['メンバーA名']} × {match['メンバーB名']}")
```

---

## エラーハンドリング戦略

### 開発環境 (ENV=development)

- API キー認証がスキップされます
- X-API-Key ヘッダーは不要です

```bash
curl -X POST http://localhost:8000/api/run-matching
```

### 本番環境 (ENV=production)

- API キー認証が必須です
- 必ず X-API-Key ヘッダーを含めてください

```bash
curl -X POST http://localhost:8000/api/run-matching \
  -H "X-API-Key: ${API_KEY}"
```

---

## 共通エラー処理パターン

### パターン1: リトライ処理

```python
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_api_with_retry(endpoint, **kwargs):
    response = requests.get(f"http://localhost:8000{endpoint}", **kwargs)
    response.raise_for_status()
    return response.json()

try:
    data = call_api_with_retry("/api/stats")
except requests.exceptions.HTTPError as e:
    print(f"API エラー: {e}")
```

### パターン2: エラーログ記録

```python
import logging

logger = logging.getLogger(__name__)

response = requests.get("http://localhost:8000/api/results")

if response.status_code != 200:
    logger.error(
        "API エラー",
        extra={
            "status_code": response.status_code,
            "error": response.json(),
            "endpoint": "/api/results"
        }
    )
```

### パターン3: ユーザーへの通知

```python
def user_friendly_error(status_code, error_detail):
    """エラーコードをユーザーフレンドリーなメッセージに変換"""
    
    if status_code == 422:
        return "入力内容を確認してください（必須フィールドが見つかりません）"
    elif status_code == 403:
        return "API 認証に失敗しました。管理者に連絡してください。"
    elif status_code == 500:
        return "サーバーに一時的な問題が発生しています。しばらく待ってから再度お試しください。"
    else:
        return f"エラーが発生しました（コード: {status_code}）"
```

---

## サポート

エラーが解決しない場合:

1. **Swagger UI で確認**: http://localhost:8000/docs
2. **ログを確認**: サーバーの stdout/stderr ログを確認
3. **環境変数を確認**: `API_KEY`, `ENV`, `ALLOWED_ORIGINS` が正しく設定されているか確認
4. **テストリクエスト**: Swagger UI の "Try it out" 機能で直接テスト

---

**最後の確認**: 2026-05-25 16:00 JST  
**作成者**: Claude Code Agent
