# API Documentation & Security - Action Plan

Generated: 2026-05-29  
Based on: `API_SWAGGER_EVALUATION.md` (Detailed evaluation report)

---

## 3-Day Action Plan to Production-Ready API Docs

### DAY 1: Security Critical Fixes (2-3 hours)

#### Task 1.1: Add Authentication to `/api/stats` [15 min]

**Current Code (main.py line ~580):**
```python
@app.get("/api/stats", tags=["Dashboard"], responses={...})
async def get_dashboard_stats():
    ...
```

**Required Change:**
```python
@app.get(
    "/api/stats", 
    tags=["Dashboard"], 
    responses={...},
    dependencies=[Depends(verify_api_key)]  # ADD THIS LINE
)
async def get_dashboard_stats(api_key: str = Depends(verify_api_key)):
    """
    ダッシュボード統計情報を取得する

    **Authentication:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます
    
    ... rest of docstring
    """
```

**Why:** Currently `/api/stats` is public - competitors can scrape match counts and metrics

---

#### Task 1.2: Add Authentication to `/api/results` [15 min]

**Current Code (main.py line ~710):**
```python
@app.get("/api/results", tags=["Matching"], responses={...})
async def get_latest_results():
    ...
```

**Required Change:**
```python
@app.get(
    "/api/results",
    tags=["Matching"],
    responses={...},
    dependencies=[Depends(verify_api_key)]  # ADD THIS LINE
)
async def get_latest_results(api_key: str = Depends(verify_api_key)):
    """
    最新のマッチング結果を取得する

    **Authentication:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます

    ... rest of docstring
    """
```

**Why:** Exposes all matching pairs and reasoning - proprietary business logic

**Testing After Change:**
```bash
# Should work with key
curl -H "X-API-Key: test-key" http://localhost:8000/api/results

# Should fail without key (in production mode)
ENV=production curl http://localhost:8000/api/results
# Expected: 422 or 403 error
```

---

#### Task 1.3: Improve Error Response Structure [30 min]

**Current:** Inconsistent error messages across endpoints

**Target:** Standardized error format

**New Model (add to main.py around line 97):**
```python
class APIError(BaseModel):
    """API エラーレスポンス"""
    error: str = Field(
        description="エラーコード（e.g. INVALID_API_KEY, ALREADY_RUNNING, VALIDATION_ERROR）"
    )
    message: str = Field(
        description="エラーメッセージ（日本語）"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="エラー発生時刻（ISO 8601）"
    )
    request_id: Optional[str] = Field(
        None,
        description="リクエスト追跡用ID"
    )
```

**Update Error Handlers (example from line ~670):**
```python
# Before:
raise HTTPException(
    status_code=403, 
    detail="無効な API キー。Render環境での認証に失敗しました。"
)

# After:
raise HTTPException(
    status_code=403,
    detail=APIError(
        error="INVALID_API_KEY",
        message="提供された API キーが無効です。本番環境での認証に失敗しました。",
        request_id=str(uuid.uuid4())
    ).model_dump()
)
```

**Update OpenAPI Responses:**
```python
responses={
    403: {
        "model": APIError,
        "description": "無効な API キー",
        "example": {
            "error": "INVALID_API_KEY",
            "message": "提供された API キーが無効です",
            "timestamp": "2026-05-29T15:30:45Z",
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    }
}
```

---

### DAY 2: Documentation Fixes (2-3 hours)

#### Task 2.1: Add Request Parameters to `/api/run-matching` [20 min]

**Location:** main.py line ~661

**Current:**
```python
@app.post("/api/run-matching", response_model=RunMatchingResponse, ...)
async def start_matching(
    background_tasks: BackgroundTasks,
    max_matches: int = 15,
    api_key: str = Depends(verify_api_key)
):
```

**Problem:** `max_matches` parameter doesn't appear in Swagger UI

**Solution:** Add parameter to function signature AND update docstring

```python
@app.post(
    "/api/run-matching",
    response_model=RunMatchingResponse,
    tags=["Matching"],
    responses={...}
)
async def start_matching(
    background_tasks: BackgroundTasks,
    max_matches: int = Query(
        15,
        ge=1,
        le=30,
        description="マッチング目標組数（1-30、デフォルト: 15）"
    ),
    api_key: str = Depends(verify_api_key)
):
    """
    AI マッチング処理を開始する

    バックグラウンドでマッチング処理を非同期実行します。

    **Parameters:**
    - max_matches: マッチング目標組数（1～30、デフォルト: 15）
    - X-API-Key: API認証キー（本番環境で必須）

    **Request Examples:**

    ```bash
    # デフォルト（15組）でマッチング開始
    curl -X POST \\
      -H "X-API-Key: your-api-key" \\
      http://localhost:8000/api/run-matching

    # 20組のマッチングを実施
    curl -X POST \\
      -H "X-API-Key: your-api-key" \\
      "http://localhost:8000/api/run-matching?max_matches=20"
    ```

    ... rest of docstring
    """
```

**Don't Forget:** Add `Query` import at top of main.py:
```python
from fastapi import FastAPI, BackgroundTasks, Request, Form, Depends, HTTPException, Header, Query
```

---

#### Task 2.2: Add Polling Strategy Documentation [15 min]

**Location:** main.py line ~719 (`get_latest_results` docstring)

**Add Section:**
```python
    """
    最新のマッチング結果を取得する

    ... existing description ...

    **Polling Strategy:**
    
    クライアントはマッチング処理の完了を確認するため、`running` フィールドを監視します。
    
    ```
    1. POST /api/run-matching を呼び出す
    2. GET /api/results を以下の間隔でポーリング:
       - 初回: 2秒待機（非同期タスク開始時間）
       - 以降: 3～5秒間隔でポーリング
    3. running == false になったら完了
    4. results フィールドから最終結果を取得
    ```

    **Expected Timings:**
    - マッチング開始～完了: 45～60秒（メンバー数による）
    - ポーリング推奨回数: 初回遅延2秒 + 15回ポーリング（5秒間隔） = 最大77秒

    **Client Implementation Example (Python):**
    
    ```python
    import requests
    import time

    API_KEY = "your-api-key"
    BASE_URL = "http://localhost:8000"
    HEADERS = {"X-API-Key": API_KEY}

    # 1. Start matching
    resp = requests.post(f"{BASE_URL}/api/run-matching", headers=HEADERS)
    assert resp.status_code == 200

    # 2. Poll for results
    time.sleep(2)  # Initial wait
    max_polls = 120  # 10 minutes with 5-second intervals
    for i in range(max_polls):
        resp = requests.get(f"{BASE_URL}/api/results", headers=HEADERS)
        data = resp.json()
        
        if not data["running"]:
            # Complete!
            matched = data["results"]["matched"]
            unmatched = data["results"]["unmatched"]
            print(f"マッチング完了: {len(matched)}組, {len(unmatched)}人不適合")
            break
        
        print(f"進行中... {data['progress']}")
        time.sleep(5)
    ```

    ... existing Notes section ...
    """
```

---

#### Task 2.3: Add Response Examples to OpenAPI [30 min]

**Location:** main.py responses definitions

**Example for `/api/run-matching` (line ~665):**

```python
@app.post(
    "/api/run-matching",
    response_model=RunMatchingResponse,
    tags=["Matching"],
    responses={
        200: {
            "model": RunMatchingResponse,
            "description": "マッチング処理を正常に開始しました",
            "example": {
                "success": True,
                "message": "マッチングを開始しました"
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "X-API-Key ヘッダーが必須です（本番環境）",
            "example": {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["header", "x-api-key"],
                        "msg": "Field required"
                    }
                ]
            }
        },
        403: {
            "model": APIError,
            "description": "無効な API キー",
            "example": {
                "error": "INVALID_API_KEY",
                "message": "提供された API キーが無効です",
                "timestamp": "2026-05-29T15:30:45Z"
            }
        },
        500: {
            "model": APIError,
            "description": "サーバー内部エラー",
            "example": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Notion API からのデータ取得に失敗しました",
                "timestamp": "2026-05-29T15:30:45Z"
            }
        }
    }
)
```

**Similar updates needed for:**
- `/api/register` (line ~252)
- `/api/register-multiactivity` (line ~410)
- `/api/stats` (line ~610)
- `/api/results` (line ~715)

---

### DAY 3: Validation & Testing (1-2 hours)

#### Task 3.1: Verify Swagger UI Rendering

**Steps:**
```bash
# 1. Start server
python main.py

# 2. Open Swagger UI in browser
# http://localhost:8000/docs

# 3. Check each endpoint displays correctly:
# - POST /api/run-matching
#   [ ] Shows "max_matches" parameter
#   [ ] Shows example request
#   [ ] Shows example responses (200, 403, 422, 500)
#
# - GET /api/results  
#   [ ] Shows authentication requirement
#   [ ] Shows example response structure
#
# - GET /api/stats
#   [ ] Shows authentication requirement (NEW)
#   [ ] Shows response schema clearly
```

---

#### Task 3.2: Test Authentication on Protected Endpoints

```bash
# Set production mode
export ENV=production
export API_KEY="test-key-12345"
python main.py &

# Test 1: /api/stats WITHOUT key (should fail)
curl http://localhost:8000/api/stats
# Expected: 422 Unprocessable Entity

# Test 2: /api/stats WITH wrong key (should fail)  
curl -H "X-API-Key: wrong-key" http://localhost:8000/api/stats
# Expected: 403 Forbidden with error_code = "INVALID_API_KEY"

# Test 3: /api/stats WITH correct key (should work)
curl -H "X-API-Key: test-key-12345" http://localhost:8000/api/stats
# Expected: 200 OK with stats data

# Test 4: /api/results protected (NEW)
curl -H "X-API-Key: test-key-12345" http://localhost:8000/api/results
# Expected: 200 OK with results structure

# Test 5: /api/register-multiactivity still PUBLIC
curl -X POST -F "名前=テスト" http://localhost:8000/api/register-multiactivity
# Expected: 200 OK (no auth required for public registration)
```

---

#### Task 3.3: Create Postman Collection

**File:** `postman_collection.json`

```json
{
  "info": {
    "name": "Blendy Matching API",
    "version": "1.0.0",
    "description": "協業マッチングシステム API クライアント"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "api_key",
      "value": "your-api-key-here"
    }
  ],
  "item": [
    {
      "name": "1. Register Member",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/register",
        "body": {
          "mode": "formdata",
          "formdata": [
            {"key": "名前", "value": "テスト太郎"},
            {"key": "会社名", "value": "テスト株式会社"}
          ]
        }
      }
    },
    {
      "name": "2. Start Matching",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/run-matching?max_matches=15",
        "header": [
          {"key": "X-API-Key", "value": "{{api_key}}"}
        ]
      }
    },
    {
      "name": "3. Poll Results (repeat until running=false)",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/results",
        "header": [
          {"key": "X-API-Key", "value": "{{api_key}}"}
        ]
      }
    }
  ]
}
```

**How to Use:**
1. Save as `postman_collection.json` in project root
2. Import into Postman: Menu → File → Import → Select this file
3. Set `{{api_key}}` variable to your actual key
4. Run requests in order (1 → 2 → 3→3→3...)

---

## Deployment Checklist

Before deploying to production (Render.com):

- [ ] `/api/stats` authentication added and tested
- [ ] `/api/results` authentication added and tested
- [ ] Error responses standardized with error codes
- [ ] POST parameters visible in Swagger UI
- [ ] Polling strategy documented
- [ ] Response examples added to Swagger
- [ ] Postman collection created and tested
- [ ] `API_KEY` secret set in Render environment
- [ ] `ENV=production` set in Render environment
- [ ] `ALLOWED_ORIGINS` set to production domain
- [ ] All endpoints tested with API key authentication enabled
- [ ] Swagger UI accessible at https://blendy-matching.onrender.com/docs

---

## Estimated Timeline

| Task | Duration | Difficulty | Dependencies |
|------|----------|-----------|--------------|
| 1.1: Auth for /api/stats | 15 min | Easy | None |
| 1.2: Auth for /api/results | 15 min | Easy | None |
| 1.3: Standardize errors | 30 min | Medium | 1.1, 1.2 complete |
| 2.1: Request params docs | 20 min | Easy | None |
| 2.2: Polling docs | 15 min | Easy | None |
| 2.3: Response examples | 30 min | Medium | None |
| 3.1: Verify Swagger | 20 min | Easy | 2.1, 2.2, 2.3 complete |
| 3.2: Auth testing | 30 min | Medium | 1.1, 1.2, 1.3 complete |
| 3.3: Postman collection | 20 min | Easy | All endpoints complete |
| **TOTAL** | **195 min (3.25 hours)** | - | - |

---

## Sign-Off Criteria

API documentation is production-ready when:

- [x] All POST endpoints have parameters documented in Swagger
- [x] All GET endpoints have authentication requirements documented
- [x] All error responses include error codes and examples
- [x] Polling strategy is documented with code examples
- [x] Response schemas have example JSON
- [x] All endpoints tested with authentication enabled
- [x] Postman collection functional for manual testing
- [x] OpenAPI schema valid per OpenAPI 3.1.0 spec
- [x] No console warnings from `http://localhost:8000/docs`

---

**Next Review:** After completing all three days of work, set a meeting to review changes against original evaluation report.

