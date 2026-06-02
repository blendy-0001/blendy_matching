"""
協業マッチングシステム
ブラウザで操作できるWebダッシュボード
起動: python main.py → http://localhost:8000 を開く
"""
from fastapi import FastAPI, BackgroundTasks, Request, Form, Depends, HTTPException, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uvicorn
import logging
import os
import traceback
import uuid

# ロギング設定（環境変数で制御）
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from notion_client import (
    get_all_members, get_matched_pairs, get_stats, save_matching_result, save_to_history,
    save_unmatched_member, create_member, create_activity,
    save_error_log, save_matching_analysis  # Phase 1: Error logs & Analysis results
)
# MARKER_TEST_2026_05_27
from matching_engine import run_matching, save_backup
from cooperation_type_recommender import infer_cooperation_type, get_cooperation_type_description

# Trigger reload to pick up matching_engine.py changes (2026-05-23 update - reloading now)

# ────────────────────────────────────────────
# Enum 定義
# ────────────────────────────────────────────

class IndustryCategory(str, Enum):
    """業種カテゴリ（会社の主要業種）"""
    IT = "IT"
    金融 = "金融"
    製造 = "製造"
    建設 = "建設"
    不動産 = "不動産"
    流通 = "流通"
    サービス = "サービス"
    医療 = "医療"
    教育 = "教育"
    メディア = "メディア"
    その他 = "その他"


class BusinessPhase(str, Enum):
    """事業フェーズ（企業の成長段階）"""
    シード = "シード"
    初期段階 = "初期段階"
    成長期 = "成長期"
    拡大期 = "拡大期"
    成熟期 = "成熟期"
    その他 = "その他"


class TargetCompanySize(str, Enum):
    """対象企業規模"""
    スタートアップ = "スタートアップ"
    中小企業 = "中小企業"
    中堅企業 = "中堅企業"
    大企業 = "大企業"
    その他 = "その他"


class Strength(str, Enum):
    """強み（活動の強み）"""
    開発 = "開発"
    営業 = "営業"
    マーケティング = "マーケティング"
    企画 = "企画"
    顧客支援 = "顧客支援"
    製造 = "製造"
    デザイン = "デザイン"
    経営 = "経営"
    コンサル = "コンサル"
    その他 = "その他"


class Challenge(str, Enum):
    """課題（活動の課題）"""
    営業 = "営業"
    マーケティング = "マーケティング"
    製造 = "製造"
    運用保守 = "運用保守"
    人材採用 = "人材採用"
    資金調達 = "資金調達"
    市場展開 = "市場展開"
    その他 = "その他"


class Position(str, Enum):
    """ポジション（活動内での役割）"""
    CEO = "CEO"
    営業 = "営業"
    マーケティング = "マーケティング"
    製品開発 = "製品開発"
    バックエンド = "バックエンド"
    フロントエンド = "フロントエンド"
    インフラ = "インフラ"
    アーキテクト = "アーキテクト"
    PM = "PM"
    その他 = "その他"


class CooperationType(str, Enum):
    """協業タイプ（推奨される協業形態）"""
    アライアンス = "アライアンス"
    業務委託 = "業務委託"
    パートナーシップ = "パートナーシップ"
    資本提携 = "資本提携"
    共同開発 = "共同開発"
    その他 = "その他"


# ────────────────────────────────────────────
# Pydantic レスポンスモデル
# ────────────────────────────────────────────

class ProgressInfo(BaseModel):
    """マッチング処理の進捗情報"""
    message: str = Field(description="進捗メッセージ（日本語）")
    percentage: int = Field(ge=0, le=100, description="進捗率（0-100）")
    current_step: str = Field(description="現在のステップ（loading_members, analyzing, saving等）")
    estimated_seconds_remaining: Optional[int] = Field(None, description="推定残り秒数（存在しない場合は null）")


class StatsData(BaseModel):
    """ダッシュボード統計情報の詳細"""
    総登録者数: int = Field(description="登録済みメンバーの総数")
    マッチング可能件数: int = Field(description="マッチング可能なペア数")
    累計マッチング済み: int = Field(description="累計マッチング済みペア数")


class StatsResponse(BaseModel):
    """ダッシュボード統計情報のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    stats: StatsData = Field(description="統計情報（総登録者数、マッチング可能件数、累計マッチング済み）")
    running: bool = Field(description="マッチング実行中フラグ")
    progress: str = Field(description="進行状況メッセージ")
    progress_info: Optional[ProgressInfo] = Field(None, description="詳細進捗情報（パーセンテージ・ステップ含む）")


class MatchingResultItem(BaseModel):
    """マッチング結果アイテム"""
    メンバーA名: str = Field(description="マッチしたメンバーA の名前")
    メンバーB名: str = Field(description="マッチしたメンバーB の名前")
    スコア: float = Field(description="相性スコア（0-100）")
    協業タイプ: str = Field(description="協業の種類")
    マッチング理由: str = Field(description="マッチング理由")
    紹介文: str = Field(description="マッチング紹介文")


class UnmatchedMember(BaseModel):
    """マッチングされなかったメンバー情報"""
    名前: str = Field(description="メンバー名")
    理由: str = Field(description="マッチされなかった理由")


class MatchingResponseData(BaseModel):
    """マッチング結果のデータ"""
    matched: List[MatchingResultItem] = Field(description="マッチングされたペア一覧")
    unmatched: List[UnmatchedMember] = Field(description="マッチングされなかったメンバー一覧")


class RunMatchingResponse(BaseModel):
    """マッチング開始のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    request_id: Optional[str] = Field(None, description="マッチング実行の追跡用ID（複数同時実行の区別に使用）")
    message: Optional[str] = Field(None, description="実行メッセージ")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class GetResultsResponse(BaseModel):
    """マッチング結果取得のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    running: bool = Field(description="マッチング実行中フラグ")
    progress: str = Field(description="進行状況メッセージ（互換性維持用）")
    progress_info: Optional[ProgressInfo] = Field(None, description="詳細進捗情報（パーセンテージ・ステップ含む）")
    results: Optional[MatchingResponseData] = Field(None, description="マッチング結果データ")


class ActivityData(BaseModel):
    """単一のアクティビティデータ（JSON body 用）"""
    名称: str = Field(description="アクティビティ名（必須）", example="Web開発サービス")
    サービス: str = Field(description="サービス内容（必須）", example="フルスタック開発・保守・運用")
    対象業界: str = Field(description="対象業界（必須）", example="金融")
    対象企業規模: Union[str, TargetCompanySize] = Field(description="対象企業規模（必須）", example="大企業")
    強み: List[Union[str, Strength]] = Field(default_factory=list, description="強みキーワード（複数選択可）", example=["開発", "API設計"])
    強み詳細: str = Field(default="", description="強みの詳細説明", example="クラウドネイティブ開発に特化しており、スケーラブルなシステム構築が得意です")
    課題: List[Union[str, Challenge]] = Field(default_factory=list, description="課題キーワード（複数選択可）", example=["運用保守"])
    課題詳細: str = Field(default="", description="課題の詳細説明", example="24時間体制のサポート人員が不足しています")
    ポジション: List[Union[str, Position]] = Field(default_factory=list, description="バリューチェーンポジション（複数選択可）", example=["バックエンド", "インフラ"])


class MemberBasicInfo(BaseModel):
    """メンバーの基本情報（JSON body 用）"""
    名前: str = Field(description="代表者名または企業名（必須）", example="テスト太郎")
    会社名: str = Field(default="", description="会社名", example="テスト会社")
    業種カテゴリ: Union[str, IndustryCategory] = Field(default="", description="業種カテゴリ（IT、金融、製造など）", example="IT")
    業種詳細: str = Field(default="", description="業種詳細（SaaS、クラウドなど）", example="SaaS")
    事業フェーズ: Union[str, BusinessPhase] = Field(default="", description="事業フェーズ（シード、成長期など）", example="成長期")
    LINE_ID: str = Field(default="", description="LINE ID（オプション）", example="line_test_123")
    Facebook_URL: str = Field(description="Facebook URL（必須）", example="https://facebook.com/test")


class RegisterMultiActivityRequest(BaseModel):
    """マルチアクティビティ登録リクエスト（JSON body）"""
    基本情報: MemberBasicInfo = Field(description="メンバーの基本情報")
    活動: List[ActivityData] = Field(
        min_items=1,
        description="アクティビティリスト（最低1個、最大3個推奨）",
        example=[
            {
                "名称": "Web開発サービス",
                "サービス": "フルスタック開発・保守",
                "対象業界": "金融",
                "対象企業規模": "大企業",
                "強み": ["開発", "API設計"],
                "強み詳細": "クラウドネイティブ開発に特化",
                "課題": ["運用保守"],
                "課題詳細": "24時間体制のサポート人員が不足",
                "ポジション": ["バックエンド", "インフラ"]
            }
        ]
    )


class RegisterMemberResponse(BaseModel):
    """メンバー登録のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    page_id: Optional[str] = Field(None, description="作成されたNotionページID")
    error: Optional[str] = Field(None, description="エラーメッセージ")
    error_code: Optional[str] = Field(None, description="エラーコード（e.g., INVALID_INPUT, DB_ERROR, NOTION_API_ERROR）")


# ────────────────────────────────────────────
# エラーレスポンスモデル
# ────────────────────────────────────────────

class ValidationErrorDetail(BaseModel):
    """バリデーションエラーの詳細"""
    type: str = Field(description="エラータイプ（e.g., 'missing', 'type_error'）")
    loc: List[str] = Field(description="エラーの位置（e.g., ['header', 'x-api-key']）")
    msg: str = Field(description="エラーメッセージ")


class ValidationErrorResponse(BaseModel):
    """422 Validation Error レスポンス"""
    detail: List[ValidationErrorDetail] = Field(description="バリデーションエラーの詳細リスト")


class AuthErrorResponse(BaseModel):
    """403 Forbidden / 401 Unauthorized レスポンス"""
    detail: str = Field(description="エラーの詳細（API キー認証失敗など）")


class InternalErrorResponse(BaseModel):
    """500 Internal Server Error レスポンス"""
    detail: str = Field(description="内部エラーのメッセージ")


class APIError(BaseModel):
    """API エラーレスポンス（統一形式）"""
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


app = FastAPI(
    title="協業マッチングシステム",
    description="AIベースの協業企業マッチングプラットフォーム API",
    version="1.0.0",
    servers=[
        {"url": "http://localhost:8000", "description": "ローカル開発環境"},
        {"url": "https://blendy-matching.onrender.com", "description": "本番環境（Render）"}
    ]
)

# OpenAPI スキーマのカスタマイズ（SecuritySchemes 定義）
def custom_openapi():
    # Note: キャッシュを使わず毎回生成する（contact/license を確実に含める）

    from fastapi.openapi.utils import get_openapi as _get_openapi

    openapi_schema = _get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )

    # info オブジェクトに contact と license を追加
    if "info" not in openapi_schema:
        openapi_schema["info"] = {}

    openapi_schema["info"]["contact"] = {
        "name": "Blendy Inc.",
        "email": "support@blendy.jp",
        "url": "https://blendy-matching.onrender.com"
    }

    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://blendy-matching.onrender.com/license"
    }

    # SecuritySchemes 定義を追加
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}

    openapi_schema["components"]["securitySchemes"]["APIKeyHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API キー認証（本番環境 ENV=production で必須）。開発環境では不要。"
    }

    # 認証が必要なエンドポイントに security 要件を追加
    protected_endpoints = [
        ("/api/run-matching", "post"),
        ("/api/results", "get"),
        ("/api/stats", "get"),
    ]

    for path, method in protected_endpoints:
        if path in openapi_schema.get("paths", {}):
            if method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"APIKeyHeader": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# OpenAPI スキーマキャッシュをクリアし、カスタム関数を割り当て
app.openapi_schema = None
app.openapi = custom_openapi

# グローバル例外ハンドラー（予期しないエラーの汎用化）
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 例外処理（詳細なエラー情報を隠す）"""
    # 意図的なエラー（認証失敗など）はそのまま返す
    if exc.status_code in [400, 401, 403, 404, 422]:
        return await http_exception_handler(request, exc)

    # 500 系エラーは詳細を隠す
    if 500 <= exc.status_code < 600:
        logger.error(f"Server error: {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": "サーバーエラーが発生しました。管理者に連絡してください。"}
        )

    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """予期しない例外の汎用ハンドラー"""
    # 詳細はログのみに記録
    logger.error(f"Unexpected error: {type(exc).__name__}: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={"detail": "予期しないエラーが発生しました。管理者に連絡してください。"}
    )

# ────────────────────────────────────────────
# セキュリティ設定
# ────────────────────────────────────────────

# CORS 設定
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# セキュリティヘッダーミドルウェア
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # キャッシュ制御ヘッダーを追加（デフォルトはキャッシュしない）
    if "cache-control" not in response.headers:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"

    return response

# API キー認証
def verify_api_key(x_api_key: str = Header(default=None, description="API キー（オプション）")):
    """
    API キー認証（オプション）

    - API_KEY が設定されている場合のみ認証を実施
    - API_KEY が設定されていない場合は、認証をスキップしてクライアントが常にフォームを利用できます

    用途：フォーム送信（/api/register-multiactivity/v2）用
    """
    api_key = os.getenv("API_KEY", "")
    env = os.getenv("ENV", "development").lower()

    logger.info(f"[verify_api_key] ENV={env}, API_KEY_configured={bool(api_key)}, x_api_key_provided={bool(x_api_key)}")

    # API_KEY が設定されていない場合は認証をスキップ（フォーム常時利用可能）
    if not api_key:
        logger.debug(f"API_KEY not configured. Skipping authentication for client accessibility.")
        return True

    # API_KEY が設定されている場合のみ認証を実施
    if not x_api_key:
        logger.warning("X-API-Key header missing")
        raise HTTPException(status_code=422, detail="X-API-Key header is required")

    if x_api_key != api_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

    logger.info("API key verification successful")
    return True


def verify_api_key_strict(x_api_key: str = Header(description="API キー（ダッシュボード・マッチング実行用・必須）")):
    """
    API キー認証（常に必須）

    - 常に API_KEY をチェックします
    - API_KEY が設定されていない場合はサーバーエラーになります
    - X-API-Key ヘッダーが必須です

    用途：ダッシュボード（/api/stats, /api/run-matching, /api/results）用
    """
    api_key = os.getenv("API_KEY", "")

    if not api_key:
        logger.error("API_KEY not configured on server - cannot authenticate dashboard access")
        raise HTTPException(status_code=500, detail="API_KEY not configured on server")

    if not x_api_key:
        logger.warning("X-API-Key header missing for dashboard access")
        raise HTTPException(status_code=401, detail="X-API-Key header is required")

    if x_api_key != api_key:
        logger.warning(f"Invalid API key attempt for dashboard")
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.info("Dashboard API key verification successful")
    return True

# マッチング実行状態の管理
matching_state = {
    "running": False,
    "request_id": None,  # マッチング実行の追跡用ID
    "progress": "",
    "progress_info": None,
    "last_result": None,
}


@app.get("/debug/env", tags=["Debug"], include_in_schema=False)
async def debug_env():
    """Debug endpoint to check environment variables (開発環境のみ）"""
    env = os.getenv("ENV", "development").lower()

    # 本番環境では 404 を返す
    if env == "production":
        logger.warning("Attempt to access /debug/env in production mode")
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "ENV": os.getenv("ENV", "not set"),
        "API_KEY_set": bool(os.getenv("API_KEY")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "not set"),
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """ダッシュボード（統計情報表示）"""
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/register-multiactivity", response_class=HTMLResponse)
async def register_multiactivity_form():
    """マルチアクティビティ対応メンバー申込フォーム"""
    with open("templates/register_multiactivity.html", encoding="utf-8") as f:
        return f.read()


@app.post(
    "/api/register-multiactivity/v2",
    response_model=RegisterMemberResponse,
    tags=["Member Management"],
    responses={
        200: {"model": RegisterMemberResponse, "description": "メンバー登録（複数アクティビティ・JSON body）が成功しました"},
        422: {"model": ValidationErrorResponse, "description": "入力バリデーションエラー"},
        500: {"model": InternalErrorResponse, "description": "メンバー登録処理中にエラーが発生しました"}
    }
)
async def register_multiactivity_v2(
    request_body: RegisterMultiActivityRequest
):
    """
    新規メンバーを登録する（マルチアクティビティ対応・JSON body版）

    JSON body で複数のアクティビティを一度に登録できます。
    フォーム形式よりも構造化されており、API クライアント実装が簡単です。

    **リクエスト形式:**
    ```json
    {
      "基本情報": {
        "名前": "テスト太郎",
        "会社名": "テスト会社",
        "業種カテゴリ": "IT",
        "業種詳細": "SaaS",
        "事業フェーズ": "成長期",
        "LINE_ID": "line_123",
        "Facebook_URL": "https://facebook.com/test"
      },
      "活動": [
        {
          "名称": "Web開発サービス",
          "サービス": "フルスタック開発・保守",
          "対象業界": "金融",
          "対象企業規模": "大企業",
          "強み": ["開発", "API設計"],
          "強み詳細": "クラウドネイティブ開発に特化",
          "課題": ["運用保守"],
          "課題詳細": "24時間体制のサポート人員が不足",
          "ポジション": ["バックエンド", "インフラ"]
        },
        {
          "名称": "マーケティング支援",
          "サービス": "デジタルマーケティング",
          "対象業界": "SaaS",
          "対象企業規模": "スタートアップ",
          "強み": ["マーケティング"],
          "強み詳細": "グロース施策に特化",
          "課題": ["営業"],
          "課題詳細": "新規顧客獲得チャネルの拡大",
          "ポジション": ["マーケティング"]
        }
      ]
    }
    ```

    **メリット:**
    - フォーム形式（/api/register-multiactivity）と異なり、構造化されたJSON body
    - OpenAPI コードジェネレータで正確なクライアントコード生成可能
    - Postman / cURL での利用が簡単
    - プログラマティックなテストが容易

    **Returns:**
    - success: 登録成功フラグ
    - page_id: 作成されたNotionページのID（成功時のみ）
    - error: エラーメッセージ（失敗時のみ）
    - error_code: エラーコード（INVALID_INPUT, DB_ERROR, NOTION_API_ERROR等）

    **Notes:**
    - このエンドポイントには認証が不要です
    - 登録後、自動的にマッチング対象に含まれます
    - 活動は最低1個、最大3個推奨です
    """
    logger.debug(f"register_multiactivity_v2 called with member: {request_body.基本情報.名前}")
    try:
        # 基本情報の構築
        基本情報 = request_body.基本情報
        data = {
            "名前": 基本情報.名前,
            "会社名": 基本情報.会社名,
            "業種カテゴリ": 基本情報.業種カテゴリ,
            "業種詳細": 基本情報.業種詳細,
            "事業フェーズ": 基本情報.事業フェーズ,
            "LINE ID": 基本情報.LINE_ID,
            "Facebook URL": 基本情報.Facebook_URL,
        }

        # アクティビティ情報を先に取得
        data["アクティビティ数"] = len(request_body.活動)
        if request_body.活動:
            data["最初のアクティビティ"] = request_body.活動[0].名称

        logger.debug("Creating member record...")
        logger.info(f"[MAIN] create_member に渡すデータ: アクティビティ数={data.get('アクティビティ数')}, 最初のアクティビティ={data.get('最初のアクティビティ')}")
        member_id = create_member(data)
        logger.info(f"メンバーレコード作成成功: {基本情報.名前} (ID: {member_id})")

        # アクティビティの作成
        activity_count = 0
        for idx, activity in enumerate(request_body.活動, start=1):
            logger.debug(f"Processing activity {idx}: {activity.名称}")

            activity_data = {
                "アクティビティ名": activity.名称,
                "サービス内容": activity.サービス,
                "強み_キーワード": activity.強み,
                "強み_詳細": activity.強み詳細,
                "課題_キーワード": activity.課題,
                "課題_詳細": activity.課題詳細,
                "バリューチェーン位置": activity.ポジション,
                "対象業界": activity.対象業界,
                "対象企業規模": activity.対象企業規模,
            }

            try:
                activity_id = create_activity(member_id, activity_data)
                logger.info(f"アクティビティ作成成功: {activity.名称} (ID: {activity_id if activity_id else 'skipped'})")
                activity_count += 1
            except Exception as activity_error:
                logger.error(f"アクティビティ作成エラー ({activity.名称}): {traceback.format_exc()}")
                continue

        logger.info(f"メンバー登録成功: {基本情報.名前} ({activity_count}個のアクティビティ)")
        return RegisterMemberResponse(success=True, page_id=member_id)

    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"マルチアクティビティ登録エラー (v2): {error_detail}")

        # エラータイプの判定
        error_type = type(e).__name__
        if "validation" in error_detail.lower() or "invalid" in error_detail.lower():
            error_code = "INVALID_INPUT"
            notion_error_type = "バリデーションエラー"
        elif "notion" in error_detail.lower():
            error_code = "NOTION_API_ERROR"
            notion_error_type = "API通信エラー"
        elif "database" in error_detail.lower():
            error_code = "DB_ERROR"
            notion_error_type = "データ不整合"
        else:
            error_code = "REGISTRATION_ERROR"
            notion_error_type = "その他"

        # Phase 1: エラーログを自動保存
        try:
            save_error_log(
                error_type=notion_error_type,
                error_message=f"メンバー登録エラー: {str(e)[:100]}",
                analysis=error_detail,
                affected_member=基本情報.名前 if '基本情報' in locals() else "",
                response_status="未対応"
            )
        except Exception as log_error:
            logger.warning(f"エラーログ保存に失敗（非致命的）: {log_error}")

        return RegisterMemberResponse(
            success=False,
            error=f"Registration failed: {error_type}",
            error_code=error_code
        )


@app.get(
    "/api/stats",
    response_model=StatsResponse,
    tags=["Dashboard"],
    dependencies=[Depends(verify_api_key_strict)],
    responses={
        200: {"model": StatsResponse, "description": "統計情報の取得に成功しました"},
        403: {"description": "無効な API キー"},
        422: {"description": "X-API-Key ヘッダーが必須です（本番環境）"},
        500: {"model": InternalErrorResponse, "description": "統計情報の取得に失敗しました"}
    }
)
async def get_dashboard_stats():
    """
    ダッシュボード統計情報を返す

    登録メンバー数、マッチング可能なペア数、実施済みマッチング数などの統計情報を取得します。

    **Authentication:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます

    **Returns:**
    - success: 統計情報取得の成功フラグ
    - stats: 統計情報（総登録者数、マッチング可能件数、累計マッチング済み）
    - running: マッチング処理が実行中かどうか
    - progress: 進行状況メッセージ

    **Notes:**
    - マッチング実行中でも常にアクセス可能です
    """
    logger.info(f"[get_dashboard_stats] Handler called (authentication passed)")
    try:
        stats_dict = get_stats()

        # StatsData オブジェクトに変換
        stats_data = StatsData(
            総登録者数=stats_dict.get("総登録者数", 0),
            マッチング可能件数=stats_dict.get("マッチング可能件数", 0),
            累計マッチング済み=stats_dict.get("累計マッチング済み", 0),
        )

        # 進捗情報の構築
        progress_info = matching_state.get("progress_info")

        return StatsResponse(
            success=True,
            stats=stats_data,
            running=matching_state["running"],
            progress=matching_state["progress"],
            progress_info=progress_info,
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"統計情報取得エラー: {error_detail}")
        # クライアントには詳細を返さない
        return StatsResponse(
            success=False,
            stats={"総登録者数": 0, "マッチング可能件数": 0, "累計マッチング済み": 0},
            running=matching_state["running"],
            progress="統計情報取得に失敗しました",
            progress_info=None,
        )


@app.post(
    "/api/run-matching",
    response_model=RunMatchingResponse,
    tags=["Matching"],
    responses={
        200: {"model": RunMatchingResponse, "description": "マッチング処理を正常に開始しました"},
        422: {"model": ValidationErrorResponse, "description": "X-API-Key ヘッダーが必須です（本番環境）"},
        403: {"model": AuthErrorResponse, "description": "無効な API キー。Render環境での認証に失敗しました。"},
        500: {"model": InternalErrorResponse, "description": "サーバー内部エラーが発生しました"}
    }
)
async def start_matching(
    background_tasks: BackgroundTasks,
    max_matches: int = Query(
        default=15,
        ge=1,
        le=30,
        description="今回のマッチング目標組数（1-30、デフォルト: 15）"
    ),
    api_key: str = Depends(verify_api_key_strict)
):
    """
    AI マッチング処理を開始する

    バックグラウンドでマッチング処理を非同期実行します。
    実行中の状態確認は `/api/results` エンドポイントで行えます。

    **認証について:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます

    **Parameters:**
    - max_matches: 今回のマッチング目標組数（1-30、デフォルト: 15）
    - X-API-Key: Render本番環境での認証キー（本番環境で必須）

    **Returns:**
    - success: True の場合、マッチング処理がバックグラウンドで開始されました
    - request_id: マッチング実行の追跡用ID
    - message: 実行メッセージ
    - message: 処理開始時の情報メッセージ
    - error: 既に実行中の場合はエラーメッセージが返ります

    **エラー処理:**
    - 422: X-API-Key ヘッダーが見つかりません（本番環境）
    - 403: 提供された X-API-Key が無効です（認証失敗）
    - 500: マッチング処理中にサーバーエラーが発生

    **完了までの時間:**
    - 小規模（5-10メンバー）: 約 10-20秒
    - 中規模（10-30メンバー）: 約 20-40秒
    - 大規模（30+メンバー）: 約 40-60秒

    **推奨ポーリング間隔:** 3-5秒
    """
    if matching_state["running"]:
        logger.warning("マッチング処理が既に実行中です")
        return RunMatchingResponse(
            success=False,
            request_id=matching_state.get("request_id"),
            error="マッチングが既に実行中です"
        )

    # 新しい request_id を生成
    request_id = f"match_{uuid.uuid4().hex[:12]}"
    matching_state["request_id"] = request_id

    background_tasks.add_task(_run_matching_task, max_matches)
    logger.info(f"マッチング処理を開始しました（Request ID: {request_id}, 目標: {max_matches}組）")
    return RunMatchingResponse(
        success=True,
        request_id=request_id,
        message="マッチングを開始しました"
    )


@app.get(
    "/api/results",
    tags=["Matching"],
    dependencies=[Depends(verify_api_key_strict)],
    responses={
        200: {"model": GetResultsResponse, "description": "マッチング結果の取得に成功しました"},
        403: {"description": "無効な API キー"},
        422: {"description": "X-API-Key ヘッダーが必須です（本番環境）"},
        500: {"model": InternalErrorResponse, "description": "マッチング結果の取得に失敗しました"}
    }
)
async def get_latest_results():
    """
    最新のマッチング結果を取得する

    マッチング処理の実行状態、進捗、および結果を取得します。
    処理実行中は progress フィールドに進行状況が返されます。

    **Authentication:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます

    **Returns:**
    - success: リクエスト成功フラグ
    - running: マッチング処理が実行中かどうか
    - progress: 進捗メッセージ
    - results: マッチング結果（処理完了時のみ含まれます）
      - matched: マッチングされたペア一覧
        - メンバーA名: マッチしたメンバーA の名前
        - メンバーB名: マッチしたメンバーB の名前
        - スコア: 相性スコア（0-100）
        - 協業タイプ: マッチのタイプ（A〜G）
        - マッチング理由: マッチが推奨される理由
        - 紹介文: 協業の提案文
      - unmatched: マッチングされなかったメンバー一覧
        - 名前: メンバー名
        - 理由: マッチされなかった理由

    **Polling Guide:**
    1. /api/run-matching でマッチング開始
    2. 3-5秒待機後、/api/results で状態確認
    3. running == false になるまで、3-5秒間隔でポーリング
    4. 通常、マッチング完了までに 30-60秒（メンバー数による）
    5. 完了後、results フィールドに最終結果が含まれます

    **ポーリング実装例（Python requests）:**
    ```python
    import time
    response = requests.post("http://localhost:8000/api/run-matching")
    while True:
        time.sleep(3)
        result = requests.get("http://localhost:8000/api/results")
        if not result.json()["running"]:
            break
    ```

    **Notes:**
    - running = true の間は results = null です
    - progress フィールドには日本語の進捗メッセージが含まれます
    - progress_info に詳細な進捗情報（パーセンテージ・ステップ）が含まれます
    """
    logger.info("get_latest_results called")
    try:
        # Build response data manually to avoid serialization issues
        result_data = None
        if matching_state.get("last_result"):
            # Ensure unmatched members have the correct format
            result_data = {
                "matched": matching_state["last_result"].get("matched", []),
                "unmatched": matching_state["last_result"].get("unmatched", [])
            }

        # 詳細進捗情報の構築
        progress_info = matching_state.get("progress_info")
        progress_info_dict = None
        if progress_info:
            progress_info_dict = {
                "message": progress_info.get("message", ""),
                "percentage": progress_info.get("percentage", 0),
                "current_step": progress_info.get("current_step", ""),
                "estimated_seconds_remaining": progress_info.get("estimated_seconds_remaining"),
            }

        response = {
            "success": True,
            "running": matching_state.get("running", False),
            "progress": matching_state.get("progress", ""),
            "progress_info": progress_info_dict,
            "results": result_data,
        }
        logger.info(f"Returning response: success={response['success']}, running={response['running']}")
        response_obj = JSONResponse(content=response)
        # キャッシュ禁止（進捗情報が頻繁に更新されるため）
        response_obj.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        return response_obj
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"マッチング結果取得エラー: {error_detail}")
        # クライアントには詳細を返さない
        response_obj = JSONResponse(
            content={"success": False, "running": False, "progress": "マッチング結果の取得に失敗しました", "progress_info": None, "results": None},
            status_code=500
        )
        response_obj.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        return response_obj


async def _run_matching_task(max_matches: int = 15):
    """
    バックグラウンドでマッチングを実行

    Args:
        max_matches: 今回のマッチング目標組数
    """
    matching_state["running"] = True
    matching_state["last_result"] = None
    matching_state["progress_info"] = None
    debug_log = []

    try:
        logger.info("🔄 マッチング処理を開始")

        # Step 1: メンバー取得
        matching_state["progress"] = "メンバーリストを読み込み中..."
        matching_state["progress_info"] = {
            "message": "メンバーリストを読み込み中...",
            "percentage": 10,
            "current_step": "loading_members",
            "estimated_seconds_remaining": None,
        }
        logger.info("メンバー取得開始")
        members = get_all_members()
        logger.info(f"メンバー取得完了: {len(members)}名")
        debug_log.append(f"✓ メンバー取得: {len(members)}名")
        matching_state["progress"] = f"{len(members)}名のデータを取得しました"
        matching_state["progress_info"] = {
            "message": f"{len(members)}名のデータを取得しました",
            "percentage": 20,
            "current_step": "loading_members_completed",
            "estimated_seconds_remaining": 50,
        }

        if len(members) == 0:
            logger.warning("⚠️ メンバーが0人です")
            debug_log.append("⚠️ 警告: メンバーが0人です")

        # Step 2: マッチング履歴取得
        matching_state["progress_info"] = {
            "message": "マッチング履歴を読み込み中...",
            "percentage": 25,
            "current_step": "loading_history",
            "estimated_seconds_remaining": 45,
        }
        matched_pairs = get_matched_pairs()
        debug_log.append(f"✓ マッチング履歴取得: {len(matched_pairs)}組")
        matching_state["progress"] = f"マッチング済み{len(matched_pairs)}組を除外します"
        matching_state["progress_info"] = {
            "message": f"マッチング済み{len(matched_pairs)}組を除外します",
            "percentage": 30,
            "current_step": "history_loaded",
            "estimated_seconds_remaining": 40,
        }

        # Step 3: AIマッチング実行
        matching_state["progress"] = f"AIがマッチングを分析中...（目標: {max_matches}組、しばらくお待ちください）"
        matching_state["progress_info"] = {
            "message": f"AIがマッチングを分析中...（目標: {max_matches}組）",
            "percentage": 50,
            "current_step": "analyzing_matches",
            "estimated_seconds_remaining": 30,
        }
        results, unmatched_members = run_matching(members, matched_pairs, max_matches=max_matches)
        debug_log.append(f"✓ マッチング実行: {len(results) if results else 0}組")
        debug_log.append(f"✓ マッチングされなかった人: {len(unmatched_members)}名")
        matching_state["progress_info"] = {
            "message": f"{len(results) if results else 0}組のマッチングを検出しました",
            "percentage": 60,
            "current_step": "analysis_completed",
            "estimated_seconds_remaining": 20,
        }

        # セッション名を定義（マッチング結果の有無に関わらず）
        session_name = f"{datetime.now().strftime('%Y年%m月')} 第{'1回' if datetime.now().day <= 15 else '2回'}"

        if not results:
            matching_state["progress"] = "マッチング可能なペアが見つかりませんでした"
            matching_state["progress_info"] = {
                "message": "マッチング可能なペアが見つかりませんでした",
                "percentage": 70,
                "current_step": "no_matches_found",
                "estimated_seconds_remaining": 10,
            }
            matching_state["last_result"] = {
                "matched": [],
                "unmatched": [
                    {
                        "名前": member["名前"],
                        "理由": "マッチング基準を満たすペアが見つかりませんでした"
                    }
                    for member in unmatched_members
                ]
            }
            debug_log.append("⚠️ マッチング結果が0件です")

            # マッチングされなかったメンバーをNotionに保存
            matching_state["progress"] = f"{len(unmatched_members)}名の未マッチメンバーをNotionに保存中..."
            matching_state["progress_info"] = {
                "message": f"{len(unmatched_members)}名の未マッチメンバーを保存中...",
                "percentage": 80,
                "current_step": "saving_unmatched",
                "estimated_seconds_remaining": 5,
            }
            for unmatched_member in unmatched_members:
                save_unmatched_member(session_name, unmatched_member)
            if unmatched_members:
                debug_log.append(f"✓ マッチングされなかったメンバー保存: {len(unmatched_members)}名")

            # バックアップもデバッグログを保存
            matching_state["progress_info"] = {
                "message": "バックアップを保存中...",
                "percentage": 95,
                "current_step": "saving_backup",
                "estimated_seconds_remaining": 2,
            }
            save_backup([], "", debug_log=debug_log)

            # Phase 1: 分析結果を自動保存（ペアなし）
            try:
                save_matching_analysis(
                    session_name=session_name,
                    matching_results=[],
                    statistics={
                        "total_matched": 0,
                        "total_members": len(members),
                        "avg_score": 0,
                        "max_score": 0,
                        "score_distribution": {"45-60": 0, "60-80": 0, "80-100": 0}
                    }
                )
                debug_log.append("✓ 分析結果を保存（ペアなし）")
            except Exception as analysis_error:
                logger.warning(f"分析結果保存に失敗（非致命的）: {analysis_error}")
                debug_log.append(f"⚠️ 分析結果保存失敗: {str(analysis_error)}")

            matching_state["progress"] = "✅ マッチング処理が完了しました（ペアなし）"
            matching_state["progress_info"] = {
                "message": "✅ マッチング処理が完了しました",
                "percentage": 100,
                "current_step": "completed",
                "estimated_seconds_remaining": 0,
            }
            return

        # Step 4: Notionに保存
        matching_state["progress"] = f"{len(results)}組をNotionに保存中..."
        matching_state["progress_info"] = {
            "message": f"{len(results)}組をNotionに保存中...",
            "percentage": 70,
            "current_step": "saving_to_notion",
            "estimated_seconds_remaining": 20,
        }

        saved_results = []
        for idx, match in enumerate(results):
            save_matching_result(session_name, match)
            save_to_history(match)
            saved_results.append({
                "メンバーA名":    match["メンバーA名"],
                "メンバーB名":    match["メンバーB名"],
                "スコア":         match["スコア"],
                "協業タイプ":     match["協業タイプ"],
                "マッチング理由": match["マッチング理由"],
                "紹介文":         match["紹介文"],
            })
            # 進捗を更新（毎10件ごと）
            if idx % 10 == 0:
                progress_pct = 70 + int((idx / len(results)) * 10)
                matching_state["progress_info"] = {
                    "message": f"{idx + 1}/{len(results)}件を保存中...",
                    "percentage": progress_pct,
                    "current_step": "saving_to_notion",
                    "estimated_seconds_remaining": 20 - int((idx / len(results)) * 10),
                }
        debug_log.append(f"✓ Notion保存: {len(results)}組")

        # マッチングされなかったメンバーをNotionに保存
        matching_state["progress_info"] = {
            "message": f"{len(unmatched_members)}名の未マッチメンバーを保存中...",
            "percentage": 85,
            "current_step": "saving_unmatched",
            "estimated_seconds_remaining": 10,
        }
        for unmatched_member in unmatched_members:
            save_unmatched_member(session_name, unmatched_member)
        if unmatched_members:
            debug_log.append(f"✓ マッチングされなかったメンバー保存: {len(unmatched_members)}名")

        # Step 5: ローカルバックアップを保存
        matching_state["progress"] = "ローカルバックアップを保存中..."
        matching_state["progress_info"] = {
            "message": "ローカルバックアップを保存中...",
            "percentage": 95,
            "current_step": "saving_backup",
            "estimated_seconds_remaining": 5,
        }
        try:
            backup_path = save_backup(results, session_name, debug_log=debug_log)
            debug_log.append(f"✓ バックアップ保存: {backup_path}")

            # Phase 1: 分析結果を自動保存（マッチング成功時）
            try:
                # スコア分布を計算
                score_dist = {"45-60": 0, "60-80": 0, "80-100": 0}
                total_score = 0
                for result in results:
                    score = result.get("スコア", 0)
                    total_score += score
                    if 45 <= score < 60:
                        score_dist["45-60"] += 1
                    elif 60 <= score < 80:
                        score_dist["60-80"] += 1
                    elif 80 <= score <= 100:
                        score_dist["80-100"] += 1

                avg_score = total_score / len(results) if results else 0

                save_matching_analysis(
                    session_name=session_name,
                    matching_results=results,
                    statistics={
                        "total_matched": len(results),
                        "total_members": len(members),
                        "avg_score": avg_score,
                        "max_score": max([r.get("スコア", 0) for r in results], default=0),
                        "score_distribution": score_dist
                    }
                )
                debug_log.append(f"✓ 分析結果を保存: {len(results)}組")
            except Exception as analysis_error:
                logger.warning(f"分析結果保存に失敗（非致命的）: {analysis_error}")
                debug_log.append(f"⚠️ 分析結果保存失敗: {str(analysis_error)}")

            matching_state["progress"] = f"✅ {len(results)}組のマッチングが完了しました！（バックアップ: {backup_path}）"
            matching_state["progress_info"] = {
                "message": f"✅ {len(results)}組のマッチングが完了しました",
                "percentage": 100,
                "current_step": "completed",
                "estimated_seconds_remaining": 0,
            }
        except Exception as backup_error:
            logger.error(f"バックアップ保存エラー: {traceback.format_exc()}")
            debug_log.append(f"⚠️ バックアップ保存に失敗: {str(backup_error)}")
            matching_state["progress"] = f"✅ {len(results)}組のマッチングが完了しました！（バックアップ保存は失敗しましたが結果は Notion に保存されています）"
            matching_state["progress_info"] = {
                "message": f"✅ {len(results)}組のマッチングが完了しました（バックアップは保存されていません）",
                "percentage": 100,
                "current_step": "completed_with_warning",
                "estimated_seconds_remaining": 0,
            }

        matching_state["last_result"] = {
            "matched": saved_results,
            "unmatched": [
                {
                    "名前": member["名前"],
                    "理由": "マッチング基準を満たすペアが見つかりませんでした"
                }
                for member in unmatched_members
            ]
        }

    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"マッチング処理エラー: {error_msg}")
        matching_state["progress"] = f"❌ エラーが発生しました: {str(e)}"
        matching_state["progress_info"] = {
            "message": f"❌ エラーが発生しました: {str(e)}",
            "percentage": 0,
            "current_step": "error",
            "estimated_seconds_remaining": None,
        }
        debug_log.append(f"❌ エラー: {error_msg}")

        # Phase 1: エラーログを自動保存
        try:
            # エラータイプを推定
            error_type = "その他"
            if "Notion API" in str(e) or "requests" in str(e):
                error_type = "API通信エラー"
            elif "JSON" in str(e) or "KeyError" in str(e):
                error_type = "データ不整合"
            elif "ValueError" in str(e) or "TypeError" in str(e):
                error_type = "バリデーションエラー"

            save_error_log(
                error_type=error_type,
                error_message=f"マッチング処理エラー: {str(e)[:100]}",
                analysis=error_msg,
                affected_member="",
                response_status="未対応"
            )
            debug_log.append(f"✓ エラーログを保存: {error_type}")
        except Exception as log_error:
            logger.warning(f"エラーログ保存に失敗（非致命的）: {log_error}")

        # エラー時もバックアップログを保存
        try:
            save_backup([], "", debug_log=debug_log)
        except Exception as backup_error:
            logger.error(f"エラー時のバックアップ保存失敗: {traceback.format_exc()}")
    finally:
        matching_state["running"] = False


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
