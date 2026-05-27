"""
協業マッチングシステム
ブラウザで操作できるWebダッシュボード
起動: python main.py → http://localhost:8000 を開く
"""
from fastapi import FastAPI, BackgroundTasks, Request, Form, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uvicorn
import logging
import os
import traceback

# ロギング設定（環境変数で制御）
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from notion_client import get_all_members, get_matched_pairs, get_stats, save_matching_result, save_to_history, save_unmatched_member, create_member, create_activity
# MARKER_TEST_2026_05_27
from matching_engine import run_matching, save_backup
from cooperation_type_recommender import infer_cooperation_type, get_cooperation_type_description

# Trigger reload to pick up matching_engine.py changes (2026-05-23 update - reloading now)

# ────────────────────────────────────────────
# Pydantic レスポンスモデル
# ────────────────────────────────────────────

class StatsResponse(BaseModel):
    """ダッシュボード統計情報のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    stats: Dict[str, Any] = Field(description="統計情報（総登録者数、マッチング可能件数、累計マッチング済み）")
    running: bool = Field(description="マッチング実行中フラグ")
    progress: str = Field(description="進行状況メッセージ")


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
    message: Optional[str] = Field(None, description="実行メッセージ")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class GetResultsResponse(BaseModel):
    """マッチング結果取得のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    running: bool = Field(description="マッチング実行中フラグ")
    progress: str = Field(description="進行状況メッセージ")
    results: Optional[MatchingResponseData] = Field(None, description="マッチング結果データ")


class RegisterMemberResponse(BaseModel):
    """メンバー登録のレスポンス"""
    success: bool = Field(description="リクエスト成功フラグ")
    page_id: Optional[str] = Field(None, description="作成されたNotionページID")
    error: Optional[str] = Field(None, description="エラーメッセージ")


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
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi as _get_openapi
    openapi_schema = _get_openapi(
        title="協業マッチングシステム",
        version="1.0.0",
        description="AIベースの協業企業マッチングプラットフォーム API",
        routes=app.routes,
    )
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

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
    return response

# API キー認証
def verify_api_key(x_api_key: str = Header(None, description="API キー（Render本番環境で必須）")):
    """
    API キー認証（本番環境で使用）

    本番環境（ENV=production）では、X-API-Key ヘッダーの値が API_KEY 環境変数と一致する必要があります。
    開発環境では認証をスキップします（テスト時に ENV=production で強制可能）。
    """
    api_key = os.getenv("API_KEY", "")
    env = os.getenv("ENV", "development").lower()

    # 本番環境（ENV=production）では必ず認証を実施
    if env == "production":
        # 本番環境では X-API-Key が必須
        if not x_api_key:
            logger.warning("X-API-Key header missing in production mode")
            raise HTTPException(status_code=422, detail="X-API-Key header is required in production mode")

        if not api_key:
            logger.warning("API_KEY is not configured in production mode")
            raise HTTPException(status_code=500, detail="API_KEY not configured")

        if x_api_key != api_key:
            logger.warning(f"Invalid API key attempt")
            raise HTTPException(status_code=403, detail="Invalid or missing API key")
        return True

    # 開発環境では認証をスキップ（テスト時にENV=productionで強制）
    logger.debug(f"Development mode: API key verification skipped (ENV={env})")
    return True

# マッチング実行状態の管理
matching_state = {
    "running": False,
    "progress": "",
    "last_result": None,
}


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """ダッシュボード画面を返す"""
    logger.debug("Dashboard にアクセスしました")
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/register", response_class=HTMLResponse)
async def register_form():
    """メンバー申込フォームを返す（AI協業タイプ推測機能搭載）"""
    with open("templates/register_new.html", encoding="utf-8") as f:
        return f.read()


@app.get("/register-multiactivity", response_class=HTMLResponse)
async def register_multiactivity_form():
    """マルチアクティビティ対応メンバー申込フォームを返す"""
    with open("templates/register_multiactivity.html", encoding="utf-8") as f:
        return f.read()


@app.post(
    "/api/register",
    response_model=RegisterMemberResponse,
    tags=["Member Management"],
    responses={
        200: {"model": RegisterMemberResponse, "description": "メンバー登録が成功しました"},
        422: {"model": ValidationErrorResponse, "description": "入力フォームのバリデーションエラー"},
        500: {"model": InternalErrorResponse, "description": "メンバー登録処理中にエラーが発生しました"}
    }
)
async def register_member(
    名前: str = Form(..., description="メンバーの名前（必須）"),
    会社名: str = Form("", description="所属会社名"),
    業種カテゴリ: str = Form("", description="業種カテゴリ"),
    業種詳細: str = Form("", description="業種の詳細"),
    主力サービス: str = Form("", description="提供している主力サービス"),
    エンドクライアント業界: str = Form("", description="エンドクライアント業界"),
    エンドクライアント規模: str = Form("", description="エンドクライアントの企業規模"),
    クライアントの課題: str = Form("", description="クライアントが抱えている課題"),
    バリューチェーン位置: List[str] = Form(default=[], description="ビジネスのバリューチェーン上の位置"),
    強み: str = Form("", description="自社の強み・得意分野"),
    課題足りないもの: str = Form("", description="自社に足りないもの・課題"),
    保有アセット: List[str] = Form(default=[], description="保有している資産・リソース"),
    事業フェーズ: str = Form("", description="現在の事業フェーズ"),
    メール: str = Form("", description="メールアドレス"),
    協業タイプ: str = Form("", description="希望する協業タイプ（A型～G型）"),
    強み_キーワード: List[str] = Form(default=[], description="強みのキーワード"),

    課題_キーワード: List[str] = Form(default=[], description="課題のキーワード"),
    LINE_ID: str = Form("", description="LINE ID"),
    Facebook_URL: str = Form("", description="Facebook URL"),
):
    """
    新規メンバーを登録する

    企業情報、サービス内容、課題などを登録フォームから送信します。
    登録情報はNotionデータベースに保存され、マッチング対象になります。

    **AI-Powered Cooperation Type Inference:**
    - 協業タイプは、ユーザーが選択するのではなく、AI が自動推測します
    - 課題感、強み、バリューチェーン位置から最適な協業パートナータイプを分析します
    - スコアリング結果と推測理由はNotionデータベースに保存されます

    **Required Fields:**
    - 名前: 企業名または代表者名（必須）

    **Optional Fields:**
    - 会社名、業種カテゴリ、業種詳細、主力サービス
    - エンドクライアント業界、エンドクライアント規模
    - クライアントの課題、強み、課題・足りないもの
    - 保有アセット、事業フェーズ、LINE ID、Facebook URL

    **Returns:**
    - success: 登録成功フラグ
    - page_id: 作成されたNotionページのID（成功時のみ）
    - error: エラーメッセージ（失敗時のみ）

    **Notes:**
    - このエンドポイントには認証が不要です
    - 登録後、自動的にマッチング対象に含まれます
    """
    logger.debug(f"register_member called with 名前={名前}")
    try:
        logger.debug("Building data dictionary...")

        # ========================================
        # AI による協業タイプの自動推測
        # ========================================
        inferred_type, type_scores, reasoning = infer_cooperation_type(
            challenges=課題_キーワード,
            strengths=強み_キーワード,
            value_chain_positions=バリューチェーン位置,
            business_phase=事業フェーズ,
            service_content=主力サービス,
        )

        type_description = get_cooperation_type_description(inferred_type)
        logger.info(f"協業タイプ自動推測: {inferred_type} ({type_description}) | 理由: {reasoning}")

        # データ辞書の構築
        data = {
            "名前": 名前,
            "会社名": 会社名,
            "業種カテゴリ": 業種カテゴリ,
            "業種詳細": 業種詳細,
            "主力サービス": 主力サービス,
            "エンドクライアント業界": エンドクライアント業界,
            "エンドクライアント規模": エンドクライアント規模,
            "クライアントの課題": クライアントの課題,
            "バリューチェーン位置": バリューチェーン位置,
            "強み": 強み,
            "強み_キーワード": 強み_キーワード,
            "課題・足りないもの": 課題足りないもの,
            "課題_キーワード": 課題_キーワード,
            "保有アセット": 保有アセット,
            "事業フェーズ": 事業フェーズ,
            "メール": メール,
            "協業タイプ": inferred_type,  # ← AI 推測値を使用
            "LINE ID": LINE_ID,
            "Facebook URL": Facebook_URL,
        }

        # 監査証跡用のロギング（Notionに保存しない）
        logger.info(f"協業タイプ推測詳細 - 推測理由: {reasoning}, スコア詳細: {type_scores}")
        logger.debug("Calling create_member...")
        page_id = create_member(data)
        logger.debug(f"create_member returned: {page_id}")
        logger.info(f"新規メンバー登録成功: {名前} (Page ID: {page_id}) | 推奨協業タイプ: {inferred_type}")
        return RegisterMemberResponse(success=True, page_id=page_id)
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"メンバー登録エラー: {error_detail}")
        print(f"REGISTRATION ERROR - Type: {type(e).__name__}")
        print(f"REGISTRATION ERROR - Message: {str(e)}")
        print(f"REGISTRATION ERROR - Traceback:\n{error_detail}")
        # Return simple ASCII error message for now
        return RegisterMemberResponse(
            success=False,
            error=f"Registration failed: {type(e).__name__}"
        )


@app.post(
    "/api/register-multiactivity",
    response_model=RegisterMemberResponse,
    tags=["Member Management"],
    responses={
        200: {"model": RegisterMemberResponse, "description": "メンバー登録（複数アクティビティ）が成功しました"},
        422: {"model": ValidationErrorResponse, "description": "入力フォームのバリデーションエラー"},
        500: {"model": InternalErrorResponse, "description": "メンバー登録処理中にエラーが発生しました"}
    }
)
async def register_member_multiactivity(request: Request):
    """
    複数の事業アクティビティを持つメンバーを登録する

    マルチアクティビティ対応フォームから送信される企業情報と複数の事業アクティビティを登録します。

    **フォーム構造:**
    - 会社基本情報: 会社名、事業フェーズ、業種カテゴリ
    - アクティビティ (最大3個): 各アクティビティに以下を含む
      - アクティビティ名、サービス内容
      - 強み: キーワード + 詳細
      - 課題: キーワード + 詳細
      - バリューチェーン位置 (複数選択可)
      - 対象業界、対象企業規模

    **Returns:**
    - success: 登録成功フラグ
    - page_id: 作成されたNotionページのID（成功時のみ）
    - error: エラーメッセージ（失敗時のみ）

    **Notes:**
    - 複数のアクティビティがある場合、全て同じメンバーに紐付けられます
    - 1人1組制限はマッチング時に適用されます
    """
    logger.debug("register_member_multiactivity called")
    try:
        form = await request.form()

        # ========================================
        # 会社基本情報の取得
        # ========================================
        会社名 = form.get("会社名", "").strip()
        事業フェーズ = form.get("事業フェーズ", "").strip()
        業種カテゴリ = form.get("業種カテゴリ", "").strip()

        # 代表者名または会社名から「名前」を決定
        代表者名 = form.get("代表者名", "").strip()
        名前 = 代表者名 or 会社名

        if not 名前:
            logger.warning("会社名または代表者名が入力されていません")
            return RegisterMemberResponse(success=False, error="会社名または代表者名が必須です")

        logger.info(f"メンバー登録開始: {名前}")

        # ========================================
        # メンバーレコード作成
        # ========================================
        member_data = {
            "名前": 名前,
            "会社名": 会社名,
            "業種カテゴリ": 業種カテゴリ,
            "事業フェーズ": 事業フェーズ,
            "協業タイプ": "",  # マルチアクティビティの場合は個別アクティビティで推測
        }

        member_id = create_member(member_data)
        if not member_id:
            logger.error("メンバーレコード作成失敗")
            return RegisterMemberResponse(success=False, error="メンバー登録に失敗しました")

        logger.info(f"メンバーレコード作成成功: {名前} (ID: {member_id})")

        # ========================================
        # アクティビティの解析と作成
        # ========================================
        activity_count = 0
        for activity_num in [1, 2, 3]:
            activity_name = form.get(f"活動{activity_num}_名称", "").strip()

            # アクティビティ名が空の場合はスキップ
            if not activity_name:
                continue

            logger.debug(f"アクティビティ {activity_num} を処理中: {activity_name}")

            # 各フィールドを取得
            service_content = form.get(f"活動{activity_num}_サービス", "").strip()

            # チェックボックス（複数値）: form.getlist() を使用
            strengths_keywords = form.getlist(f"活動{activity_num}_強み")
            challenges_keywords = form.getlist(f"活動{activity_num}_課題")
            value_chain = form.getlist(f"活動{activity_num}_バリューチェーン")

            # テキストフィールド（単一値）
            strengths_detail = form.get(f"活動{activity_num}_強み詳細", "").strip()
            challenges_detail = form.get(f"活動{activity_num}_課題詳細", "").strip()
            target_industry = form.get(f"活動{activity_num}_対象業界", "").strip()
            target_size = form.get(f"活動{activity_num}_対象企業規模", "").strip()

            # アクティビティデータ構築
            activity_data = {
                "アクティビティ名": activity_name,
                "サービス内容": service_content,
                "強み_キーワード": strengths_keywords,
                "強み_詳細": strengths_detail,
                "課題_キーワード": challenges_keywords,
                "課題_詳細": challenges_detail,
                "バリューチェーン位置": value_chain,
                "対象業界": target_industry,
                "対象企業規模": target_size,
            }

            # アクティビティ作成
            try:
                activity_id = create_activity(member_id, activity_data)
                if activity_id:
                    logger.info(f"アクティビティ作成成功: {activity_name} (ID: {activity_id})")
                    activity_count += 1
                else:
                    logger.warning(f"アクティビティ作成失敗（ID取得できず）: {activity_name}")
            except Exception as activity_error:
                logger.error(f"アクティビティ作成エラー ({activity_name}): {traceback.format_exc()}")
                # 1個のアクティビティ失敗でメンバー全体を失敗にしない
                continue

        if activity_count == 0:
            logger.warning(f"メンバー {名前} にアクティビティが1つも登録されていません")
            return RegisterMemberResponse(
                success=False,
                error="最低1つのアクティビティを入力してください"
            )

        logger.info(f"メンバー {名前} を {activity_count} 個のアクティビティで登録成功")
        return RegisterMemberResponse(success=True, page_id=member_id)

    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"マルチアクティビティ登録エラー: {error_detail}")
        return RegisterMemberResponse(
            success=False,
            error=f"Registration failed: {type(e).__name__}"
        )


@app.get(
    "/api/stats",
    response_model=StatsResponse,
    tags=["Dashboard"],
    responses={
        200: {"model": StatsResponse, "description": "統計情報の取得に成功しました"},
        500: {"model": InternalErrorResponse, "description": "統計情報の取得に失敗しました"}
    }
)
async def get_dashboard_stats():
    """
    ダッシュボード統計情報を返す

    登録メンバー数、マッチング可能なペア数、実施済みマッチング数などの統計情報を取得します。

    **Returns:**
    - success: 統計情報取得の成功フラグ
    - stats: 統計情報（総登録者数、マッチング可能件数、累計マッチング済み）
    - running: マッチング処理が実行中かどうか
    - progress: 進行状況メッセージ

    **Notes:**
    - このエンドポイントには認証が不要です
    - マッチング実行中でも常にアクセス可能です
    """
    try:
        stats = get_stats()
        return StatsResponse(
            success=True,
            stats=stats,
            running=matching_state["running"],
            progress=matching_state["progress"],
        )
    except Exception as e:
        logger.error(f"統計情報取得エラー: {traceback.format_exc()}")
        return StatsResponse(
            success=False,
            stats={"総登録者数": 0, "マッチング可能件数": 0, "累計マッチング済み": 0},
            running=matching_state["running"],
            progress=matching_state["progress"],
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
    max_matches: int = 15,
    api_key: str = Depends(verify_api_key)
):
    """
    AI マッチング処理を開始する

    バックグラウンドでマッチング処理を非同期実行します。
    実行中の状態確認は `/api/results` エンドポイントで行えます。

    **認証について:**
    - 本番環境（ENV=production）では、X-API-Key ヘッダーが必須です
    - 開発環境ではスキップされます

    **Parameters:**
    - max_matches: 今回のマッチング目標組数（デフォルト: 15、最大30）
    - X-API-Key: Render本番環境での認証キー（本番環境で必須）

    **Returns:**
    - success: True の場合、マッチング処理がバックグラウンドで開始されました
    - message: 処理開始時の情報メッセージ
    - error: 既に実行中の場合はエラーメッセージが返ります

    **エラー処理:**
    - 422: X-API-Key ヘッダーが見つかりません（本番環境）
    - 403: 提供された X-API-Key が無効です（認証失敗）
    - 500: マッチング処理中にサーバーエラーが発生
    """
    if matching_state["running"]:
        logger.warning("マッチング処理が既に実行中です")
        return RunMatchingResponse(success=False, error="マッチングが既に実行中です")

    background_tasks.add_task(_run_matching_task, max_matches)
    logger.info(f"マッチング処理を開始しました（目標: {max_matches}組）")
    return RunMatchingResponse(success=True, message="マッチングを開始しました")


@app.get(
    "/api/results",
    tags=["Matching"],
    responses={
        200: {"model": GetResultsResponse, "description": "マッチング結果の取得に成功しました"},
        500: {"model": InternalErrorResponse, "description": "マッチング結果の取得に失敗しました"}
    }
)
async def get_latest_results():
    """
    最新のマッチング結果を取得する

    マッチング処理の実行状態、進捗、および結果を取得します。
    処理実行中は progress フィールドに進行状況が返されます。

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
    2. /api/results で running == false まで定期的にポーリング
    3. 完了後、results フィールドに最終結果が含まれます

    **Notes:**
    - このエンドポイントには認証が不要です
    - running = true の間は results = null です
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

        response = {
            "success": True,
            "running": matching_state.get("running", False),
            "progress": matching_state.get("progress", ""),
            "results": result_data,
        }
        logger.info(f"Returning response: {response}")
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in get_latest_results: {traceback.format_exc()}")
        return JSONResponse(content={"success": False, "running": False, "progress": "Error", "results": None}, status_code=500)


async def _run_matching_task(max_matches: int = 15):
    """
    バックグラウンドでマッチングを実行

    Args:
        max_matches: 今回のマッチング目標組数
    """
    matching_state["running"] = True
    matching_state["last_result"] = None
    debug_log = []

    try:
        logger.info("🔄 マッチング処理を開始")

        # Step 1: メンバー取得
        matching_state["progress"] = "メンバーリストを読み込み中..."
        logger.info("メンバー取得開始")
        members = get_all_members()
        logger.info(f"メンバー取得完了: {len(members)}名")
        debug_log.append(f"✓ メンバー取得: {len(members)}名")
        matching_state["progress"] = f"{len(members)}名のデータを取得しました"

        if len(members) == 0:
            logger.warning("⚠️ メンバーが0人です")
            debug_log.append("⚠️ 警告: メンバーが0人です")

        # Step 2: マッチング履歴取得
        matched_pairs = get_matched_pairs()
        debug_log.append(f"✓ マッチング履歴取得: {len(matched_pairs)}組")
        matching_state["progress"] = f"マッチング済み{len(matched_pairs)}組を除外します"

        # Step 3: AIマッチング実行
        matching_state["progress"] = f"AIがマッチングを分析中...（目標: {max_matches}組、しばらくお待ちください）"
        results, unmatched_members = run_matching(members, matched_pairs, max_matches=max_matches)
        debug_log.append(f"✓ マッチング実行: {len(results) if results else 0}組")
        debug_log.append(f"✓ マッチングされなかった人: {len(unmatched_members)}名")

        # セッション名を定義（マッチング結果の有無に関わらず）
        session_name = f"{datetime.now().strftime('%Y年%m月')} 第{'1回' if datetime.now().day <= 15 else '2回'}"

        if not results:
            matching_state["progress"] = "マッチング可能なペアが見つかりませんでした"
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
            for unmatched_member in unmatched_members:
                save_unmatched_member(session_name, unmatched_member)
            if unmatched_members:
                debug_log.append(f"✓ マッチングされなかったメンバー保存: {len(unmatched_members)}名")

            # バックアップもデバッグログを保存
            save_backup([], "", debug_log=debug_log)
            matching_state["progress"] = "✅ マッチング処理が完了しました（ペアなし）"
            return

        # Step 4: Notionに保存
        matching_state["progress"] = f"{len(results)}組をNotionに保存中..."

        saved_results = []
        for match in results:
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
        debug_log.append(f"✓ Notion保存: {len(results)}組")

        # マッチングされなかったメンバーをNotionに保存
        for unmatched_member in unmatched_members:
            save_unmatched_member(session_name, unmatched_member)
        if unmatched_members:
            debug_log.append(f"✓ マッチングされなかったメンバー保存: {len(unmatched_members)}名")

        # Step 5: ローカルバックアップを保存
        matching_state["progress"] = "ローカルバックアップを保存中..."
        try:
            backup_path = save_backup(results, session_name, debug_log=debug_log)
            matching_state["progress"] = f"✅ {len(results)}組のマッチングが完了しました！（バックアップ: {backup_path}）"
        except Exception as backup_error:
            logger.error(f"バックアップ保存エラー: {traceback.format_exc()}")
            debug_log.append(f"⚠️ バックアップ保存に失敗: {str(backup_error)}")
            matching_state["progress"] = f"✅ {len(results)}組のマッチングが完了しました！（バックアップ保存は失敗しましたが結果は Notion に保存されています）"

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
        debug_log.append(f"❌ エラー: {error_msg}")
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
