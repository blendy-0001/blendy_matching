"""
協業マッチングシステム
ブラウザで操作できるWebダッシュボード
起動: python main.py → http://localhost:8000 を開く
"""
from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List, Optional
import uvicorn

from notion_client import get_all_members, get_matched_pairs, get_stats, save_matching_result, save_to_history, create_member
from matching_engine import run_matching

app = FastAPI(title="協業マッチングシステム")

# マッチング実行状態の管理
matching_state = {
    "running": False,
    "progress": "",
    "last_result": None,
}


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """ダッシュボード画面を返す"""
    print("[DEBUG] Dashboard accessed")
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
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


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
        return {"success": False, "error": str(e)}


@app.post("/api/run-matching")
async def start_matching(background_tasks: BackgroundTasks):
    """マッチングを開始する"""
    if matching_state["running"]:
        return JSONResponse({"success": False, "error": "マッチングが既に実行中です"})

    background_tasks.add_task(_run_matching_task)
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


async def _run_matching_task():
    """バックグラウンドでマッチングを実行"""
    matching_state["running"] = True
    matching_state["last_result"] = None
    try:
        # Step 1: メンバー取得
        matching_state["progress"] = "メンバーリストを読み込み中..."
        members = get_all_members()
        matching_state["progress"] = f"{len(members)}名のデータを取得しました"

        # Step 2: マッチング履歴取得
        matched_pairs = get_matched_pairs()
        matching_state["progress"] = f"マッチング済み{len(matched_pairs)}組を除外します"

        # Step 3: AIマッチング実行
        matching_state["progress"] = "AIがマッチングを分析中...（しばらくお待ちください）"
        results = run_matching(members, matched_pairs)

        if not results:
            matching_state["progress"] = "マッチング可能なペアが見つかりませんでした"
            matching_state["last_result"] = []
            return

        # Step 4: Notionに保存
        session_name = f"{datetime.now().strftime('%Y年%m月')} 第{'1回' if datetime.now().day <= 15 else '2回'}"
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

        matching_state["last_result"] = saved_results
        matching_state["progress"] = f"✅ {len(results)}組のマッチングが完了しました！"

    except Exception as e:
        matching_state["progress"] = f"❌ エラーが発生しました: {str(e)}"
    finally:
        matching_state["running"] = False


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
