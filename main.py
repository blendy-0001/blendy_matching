"""
協業マッチングシステム
ブラウザで操作できるWebダッシュボード
起動: python main.py → http://localhost:8000 を開く
"""
from fastapi import FastAPI, BackgroundTasks, Request, Form, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
import uvicorn
import logging
import os
import traceback

# ロギング設定（環境変数で制御）
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from notion_client import get_all_members, get_matched_pairs, get_stats, save_matching_result, save_to_history, save_unmatched_member, create_member
from matching_engine import run_matching, save_backup

# Trigger reload to pick up matching_engine.py changes (2026-05-23 update - reloading now)

app = FastAPI(title="協業マッチングシステム")

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
def verify_api_key(x_api_key: str = Header(None)):
    """API キー認証（本番環境で使用）"""
    api_key = os.getenv("API_KEY", "")

    # ローカル開発環境では認証をスキップ
    if os.getenv("ENV", "development") == "development":
        return True

    # 本番環境では API キーが必須
    if not api_key:
        # API キーが設定されていない場合は認証をスキップ
        logger.warning("⚠️ API_KEY が設定されていません")
        return True

    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
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
    """メンバー申込フォームを返す"""
    with open("templates/register.html", encoding="utf-8") as f:
        return f.read()


@app.post("/api/register")
async def register_member(
    名前: str = Form(...),
    会社名: str = Form(""),
    業種カテゴリ: str = Form(""),
    業種詳細: str = Form(""),
    主力サービス: str = Form(""),
    エンドクライアント業界: str = Form(""),
    エンドクライアント規模: str = Form(""),
    クライアントの課題: str = Form(""),
    バリューチェーン位置: List[str] = Form(default=[]),
    強み: str = Form(""),
    課題足りないもの: str = Form(""),
    保有アセット: List[str] = Form(default=[]),
    事業フェーズ: str = Form(""),
    LINE_ID: str = Form(""),
    Facebook_URL: str = Form(""),
):
    """フォーム送信を受け取りNotionに登録"""
    try:
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
            "課題・足りないもの": 課題足りないもの,
            "保有アセット": 保有アセット,
            "事業フェーズ": 事業フェーズ,
            "LINE ID": LINE_ID,
            "Facebook URL": Facebook_URL,
        }
        page_id = create_member(data)
        return JSONResponse({"success": True, "page_id": page_id})
    except Exception as e:
        logger.error(f"メンバー登録エラー: {traceback.format_exc()}")
        return JSONResponse(
            {"success": False, "error": "メンバー登録に失敗しました。入力内容を確認してください。"},
            status_code=500
        )


@app.get("/api/stats")
async def get_dashboard_stats():
    """ダッシュボード統計情報を返す"""
    try:
        stats = get_stats()
        return {
            "success": True,
            "stats": stats,
            "running": matching_state["running"],
            "progress": matching_state["progress"],
        }
    except Exception as e:
        logger.error(f"統計情報取得エラー: {traceback.format_exc()}")
        return {
            "success": False,
            "error": "統計情報の取得に失敗しました",
            "stats": {"総登録者数": 0, "マッチング可能件数": 0, "累計マッチング済み": 0},
            "running": matching_state["running"],
            "progress": matching_state["progress"],
        }


@app.post("/api/run-matching")
async def start_matching(background_tasks: BackgroundTasks, max_matches: int = 15, api_key: str = Depends(verify_api_key)):
    """
    マッチングを開始する

    Args:
        max_matches: 今回のマッチング目標組数（デフォルト: 15）
        api_key: API キー認証（Header: X-API-Key）
    """
    if matching_state["running"]:
        return JSONResponse({"success": False, "error": "マッチングが既に実行中です"})

    background_tasks.add_task(_run_matching_task, max_matches)
    return {"success": True, "message": "マッチングを開始しました"}


@app.get("/api/results")
async def get_latest_results():
    """最新のマッチング結果を返す"""
    return {
        "success": True,
        "running": matching_state["running"],
        "progress": matching_state["progress"],
        "results": matching_state["last_result"],
    }


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
                "unmatched": unmatched_members
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
            "unmatched": unmatched_members
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
