# Swagger UI API Documentation - Client Evaluation Report

**Evaluation Date:** 2026-05-29  
**API Version:** 1.0.0  
**Server:** http://localhost:8000/docs  

---

## Executive Summary

The Swagger/OpenAPI documentation is **well-structured at core endpoints but has critical inconsistencies in security implementation and request documentation**. While response models are clearly defined, several important gaps reduce client usability and create confusion around authentication requirements.

**Overall Assessment:** ⚠️ **GOOD with Critical Issues**
- ✓ Well-documented response schemas
- ✓ Clear endpoint descriptions
- ⚠️ Authentication implementation vs. documentation mismatch
- ✗ Missing request body documentation for key endpoints

---

## Detailed Findings

### [1] SECURITY ARCHITECTURE

#### API Key Authentication Status

**What's Documented:**
- OpenAPI schema correctly declares `APIKeyHeader` security scheme (X-API-Key, header-based)
- Proper 403/422 error responses documented for `/api/run-matching`

**What's Actually Implemented:**
- ✓ `verify_api_key()` function defined and functional
- ✓ Dependency injection on `/api/run-matching` endpoint
- ✓ Production mode (ENV=production) triggers mandatory authentication
- ✓ Development mode (default) skips authentication for testing
- ✓ Security headers middleware added (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS)
- ✓ CORS middleware configured with allowed origins from environment variable

**Critical Issues:**

| Endpoint | Documented | Implemented | Risk |
|----------|-----------|------------|------|
| `/api/register` | No Auth | No Auth | ✓ OK (public registration intentional) |
| `/api/register-multiactivity` | No Auth | No Auth | ✓ OK (public registration intentional) |
| `/api/stats` | No Auth | **No Auth** | ⚠️ **ISSUE: Stats are public** |
| `/api/run-matching` | ✓ Auth Required | ✓ Auth Required | ✓ OK |
| `/api/results` | No Auth | **No Auth** | ⚠️ **ISSUE: Results are public** |

**Problem:** `/api/stats` and `/api/results` expose all matching data without authentication. This allows:
- Competitors to scrape matching results
- Unintended data exposure to the public
- No audit trail for who accessed sensitive matching information

**Recommendation:**
```python
# Add authentication to /api/stats and /api/results
@app.get("/api/stats", dependencies=[Depends(verify_api_key)])
async def get_stats():
    ...

@app.get("/api/results", dependencies=[Depends(verify_api_key)])  
async def get_latest_results():
    ...
```

---

### [2] DOCUMENTATION QUALITY

#### Request Documentation

**Good Examples:**
```
POST /api/register
- All 22 form parameters documented with descriptions
- Required vs. optional fields clearly marked
- Good field-level descriptions (e.g., "企業名または代表者名（必須）")
```

**Problem Areas:**

1. **Missing Request Body for `/api/run-matching`**
   - Endpoint declares it's a POST but shows no request parameters in Swagger UI
   - Parameter `max_matches: int = 15` is NOT visible in OpenAPI schema
   - Client has no way to know they can pass `max_matches` parameter

   **Impact:** Clients will call the endpoint without max_matches parameter, getting default value (15) without realizing it's configurable.

2. **No Query Parameter Documentation for `/api/results`**
   - GET endpoint with no documented parameters
   - Polling strategy is described in docstring but not in formal schema

#### Response Documentation

**Strengths:**
- ✓ Detailed response models for all main endpoints
- ✓ Clear field descriptions with Japanese labels
- ✓ Nested object structures properly documented (MatchingResultItem, UnmatchedMember)
- ✓ Error responses (422, 403, 500) documented with proper descriptions

**Issue:**
- Response examples would improve clarity (Swagger shows only schema, not example JSON)

#### Overall Coverage
- **Documented endpoints:** 5 out of 10 paths have descriptions
- **Undocumented:** `/` (Dashboard), `/register`, `/register-multiactivity` return HTML, not API

---

### [3] ENDPOINT DESIGN & PRACTICALITY

#### Strengths

**1. Clear Workflow Design**
```
Flow: Register → Run Matching → Poll Results → Get Results
```
The three-step API workflow is intuitive and documented in `/api/results` docstring.

**2. Good Response Models**
- `MatchingResultItem` provides comprehensive match info: name, score, cooperation type, reason, intro text
- `UnmatchedMember` explains why members couldn't be matched
- `StatsResponse` returns actionable metrics: registered count, matchable pairs, total matches

**3. Separation of Concerns**
- Member management (`/api/register*`) is separate from matching operations
- Polling pattern allows asynchronous processing without blocking

#### Weaknesses

**1. Async Polling Reliability**
- How long should client wait between `/api/results` polls?
- No documented timeout or expected completion time
- Client might poll too frequently (overload) or too infrequently (poor UX)

**2. Single Result Storage**
- `GET /api/results` returns `matching_state["last_result"]`
- No versioning or historical results
- If client misses results before next matching run, data is lost

**Recommendation:** Add timestamp to results:
```python
{
  "success": True,
  "running": False,
  "progress": "...",
  "results": {...},
  "completed_at": "2026-05-29T15:30:45Z",  # NEW
  "execution_time_seconds": 47.3             # NEW
}
```

**3. No Rate Limiting Documentation**
- Can client call `/api/run-matching` immediately after previous match completes?
- Is there a minimum time between runs?
- Is there a max matches per day?

---

### [4] SECURITY CONCERNS

#### Critical Issues

**1. Public Data Exposure (HIGH RISK)**
```
GET /api/stats        → Anyone can see total members & matches
GET /api/results      → Anyone can see all matching pairs & recommendations
```
This exposes:
- Competitive intelligence (which companies are being matched)
- All internal reasoning & match scores
- Unmatched members and their profiles

**2. Authentication Disabled in Development**
```python
if env == "production":
    # Auth enforced
else:
    # Auth skipped - returns True immediately
```
This is fine for local dev, but risky if:
- Developer deploys to staging with ENV != "production"
- Staging URL gets accidentally public
- Custom deployments ignore ENV configuration

**Fix:** Make authentication always required by default, allow opt-out with a flag:
```python
DISABLE_AUTH_FOR_DEV = os.getenv("DISABLE_AUTH_FOR_DEV", "false").lower() == "true"

if api_key != expected_key:
    if not DISABLE_AUTH_FOR_DEV:
        raise HTTPException(403, "Invalid key")
```

**3. API Key in Headers (Good) but No Rate Limiting**
- API key prevents basic unauthorized access
- But no rate limiting on authenticated requests
- Single compromised key could trigger many expensive matching operations

**4. No Audit Logging of Auth Failures**
```python
logger.warning("Invalid API key attempt")  # Only warning, no details
```
- Doesn't log which IP/client attempted
- Doesn't log the attempted key value (for comparison to known keys)
- No structured audit trail for compliance

#### Medium Issues

**1. CORS Configuration**
```python
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
```
- ✓ Good: Configurable via environment variable
- ⚠️ Risky: Default is too permissive (localhost only OK for dev, but allow_methods=["GET", "POST"] with allow_headers=["*"])
- ⚠️ Consider: Restrict headers to specific list instead of ["*"]

**2. No HTTPS Enforcement Documentation**
- HSTS header set correctly (31536000 seconds = 1 year)
- But if client connects via HTTP (not HTTPS), the header isn't useful
- No documented requirement for HTTPS in API description

---

### [5] CLIENT EXPERIENCE ISSUES

#### Pain Points

**1. Discovery of Request Parameters**
- Swagger shows `POST /api/run-matching` but no visual parameter input
- Client must read docstring to learn about `max_matches` parameter
- Some clients might not even try because Swagger shows "no params"

**Fix:** Add openapi_extra to include parameters in schema:
```python
@app.post(
    "/api/run-matching",
    openapi_extra={
        "parameters": [
            {
                "name": "max_matches",
                "in": "query",
                "required": False,
                "schema": {"type": "integer", "default": 15, "minimum": 1, "maximum": 30},
                "description": "Target number of match pairs"
            }
        ]
    }
)
```

**2. No Server Environment Indicator in Swagger**
- Swagger shows both servers (localhost + production URL) with equal prominence
- Client might not know which server is active
- Production URL (blendy-matching.onrender.com) listed but no ENV indicator

**3. Response Format Inconsistency**
- Some responses use Japanese field names (メンバーA名, スコア)
- Some use English (success, running, error)
- Inconsistent naming makes JSON parsing harder in non-Japanese clients

**4. Missing Error Examples**
```
Error Response:
- 422: "X-API-Key ヘッダーが必須です（本番環境）"
- 403: "無効な API キー"
- 500: "サーバー内部エラーが発生しました"
```
- No example response bodies
- Client can't programmatically detect error type (only HTTP status code)
- No error codes/identifiers for automated handling

**Better Format:**
```json
{
  "error": "INVALID_API_KEY",
  "message": "The provided X-API-Key header is invalid",
  "details": {
    "expected_length": 32,
    "provided_length": 8
  }
}
```

---

### [6] OPENAPI SCHEMA ISSUES

#### Detected Problems

**1. Automatic OpenAPI Generation Limitation**
```python
def custom_openapi():
    # Manual schema manipulation needed because FastAPI auto-generation is limited
```
This workaround suggests:
- FastAPI's automatic security scheme detection isn't working properly
- Manual intervention required for production-grade schema
- Risk of schema drifting from actual implementation

**2. Missing Global Security (Although Endpoints Have It)**
```python
# In OpenAPI schema:
# "security": [] at root level = NO GLOBAL AUTH

# But individual endpoints like /api/run-matching DO have auth
# This creates false sense that most endpoints are unprotected
```

**3. Inconsistent Path Documentation**
- `/api/register*` endpoints documented in POST handler docstrings
- But schema shows HTML endpoints (`/register`, `/register-multiactivity`) as separate paths
- Client might think there are form endpoints (which there are, but they serve HTML)

---

## Compliance & Standards

### OpenAPI 3.1.0 Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| Info Object | ✓ | Title, version, description present |
| Servers | ✓ | Both localhost and production documented |
| Paths | ✓ | All endpoints defined |
| Components/Schemas | ✓ | Request/response schemas complete |
| SecuritySchemes | ✓ | APIKeyHeader properly defined |
| Security (Global) | ✗ | Not applied globally (should be at path level) |
| Parameters | ⚠️ | POST body parameters documented but query params missing |
| Responses | ✓ | Main responses documented, error examples missing |

### Best Practices Gap

| Practice | Current | Expected |
|----------|---------|----------|
| Request validation examples | ✗ | Example requests for each POST |
| Response examples | ✗ | Example JSON for each response type |
| Error standardization | ✗ | Consistent error structure with codes |
| Rate limiting | ✗ | Documented rate limits |
| Versioning | ✗ | API version in URL (v1/v2) |
| Pagination | N/A | /api/results doesn't paginate |
| Idempotency | ✗ | No mention of idempotency keys |

---

## Recommendations (Priority Order)

### CRITICAL (Fix Before Production)

**1. Add Authentication to `/api/stats` and `/api/results`**
```python
@app.get(
    "/api/stats",
    dependencies=[Depends(verify_api_key)],  # ADD THIS
    tags=["Dashboard"],
    responses={...}
)
```
**Impact:** Prevents unauthorized data access  
**Effort:** 5 minutes  
**User Friction:** Low (internal client scripts already use API key)

**2. Document POST Body Parameters for `/api/run-matching`**
```python
@app.post(
    "/api/run-matching",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "max_matches": {
                                "type": "integer",
                                "default": 15,
                                "description": "Target number of matching pairs"
                            }
                        }
                    }
                }
            }
        }
    }
)
```
**Impact:** Clients discover parameter in Swagger UI  
**Effort:** 10 minutes  
**User Friction:** None (improves discoverability)

**3. Standardize Error Responses**
```python
class APIErrorResponse(BaseModel):
    error: str  # Error code: "INVALID_API_KEY", "ALREADY_RUNNING", etc.
    message: str  # Human readable message
    timestamp: datetime
    request_id: Optional[str] = None
```
**Impact:** Clients can programmatically handle errors  
**Effort:** 20 minutes  
**User Friction:** Breaking change (responses change format)

### HIGH (Fix Before Next Release)

**4. Add Response Examples to OpenAPI Schema**
```python
responses={
    200: {
        "model": RunMatchingResponse,
        "example": {
            "success": True,
            "message": "マッチングを開始しました"
        }
    }
}
```
**Impact:** Swagger UI shows example data  
**Effort:** 15 minutes per endpoint  
**User Friction:** None (informational only)

**5. Document Polling Strategy & Timeouts**
Add to `/api/results` docstring:
```
**Polling Recommendations:**
- Initial wait: 2 seconds (let async task start)
- Poll interval: 3-5 seconds
- Max retries: 120 (≈10 minutes timeout)
- Expected completion: 45-60 seconds for 15 matches
```
**Impact:** Clients understand expected behavior  
**Effort:** 5 minutes  
**User Friction:** None (guidance only)

**6. Add API Key Scope/Permissions Documentation**
```
**API Key Permissions:**
- POST /api/register: PUBLIC (no key required)
- POST /api/register-multiactivity: PUBLIC (no key required)
- GET /api/stats: REQUIRES KEY (production)
- POST /api/run-matching: REQUIRES KEY (production)
- GET /api/results: REQUIRES KEY (production)
```
**Impact:** Clear permissions per endpoint  
**Effort:** 10 minutes  
**User Friction:** None (clarification only)

### MEDIUM (Future Improvements)

**7. Add Request/Response Size Limits**
- Max JSON body size: document it
- Max results count: document pagination strategy (if adding)
- Max concurrent requests: document rate limits

**8. Add Versioning Strategy**
- Current: No API version indicator
- Recommended: Add /v1/ to paths or use Accept header

**9. Add Webhook Support (if needed)**
- Instead of polling, server could POST results to client webhook
- Would reduce load and improve UX

---

## Client Integration Checklist

**Before integrating with this API, clients should:**

- [ ] Set `ENV=production` and `API_KEY=<secret>` environment variables
- [ ] Understand that X-API-Key header is required for `/api/run-matching`, `/api/stats`, `/api/results`
- [ ] Implement polling with 3-5 second intervals on `/api/results`
- [ ] Handle 403 Forbidden responses (invalid API key)
- [ ] Handle 422 Unprocessable Entity (missing or malformed request)
- [ ] Handle 500 Internal Server Error (Notion API timeout or failure)
- [ ] Expect 45-60 second completion time for matching operation
- [ ] Don't rely on historical results (only last result is stored)
- [ ] Don't call `/api/run-matching` twice concurrently (will return error)

---

## Summary Table

| Category | Rating | Key Issue | Fix |
|----------|--------|-----------|-----|
| Security | 🟡 MEDIUM | `/api/stats` & `/api/results` public | Add auth dependency |
| Documentation | 🟡 MEDIUM | POST params not in schema | Add openapi_extra |
| Usability | 🟢 GOOD | Clear workflow & models | Minor improvements |
| Compliance | 🟡 MEDIUM | Error format inconsistent | Standardize responses |
| Error Handling | 🟡 MEDIUM | No error codes | Add error codes to responses |
| Examples | 🔴 POOR | No request/response examples | Add JSON examples |

---

**Overall:** The API is functional and well-intentioned but needs security improvements and better Swagger documentation before production use. The core endpoint design is solid; fixes are mostly in documentation and security enforcement.

