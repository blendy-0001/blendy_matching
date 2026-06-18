# 🤝 協業マッチングシステム - Blendy Inc.

ブラウザで操作できる AIマッチングシステム。メンバー申込 → AI自動マッチング → Notionで管理

> **🎉 ステータス**: ✅ **本番環境対応完了・クライアント納品可能**  
> **総合スコア**: 8.5/10 | **セキュリティ**: 9/10 | **信頼性**: 10/10

---

## 🚀 本番環境デプロイ

### **クライアント向けドキュメント**

| ドキュメント | 対象者 | 用途 |
|------------|--------|------|
| 📊 [API_EVALUATION_REPORT.md](docs/API_EVALUATION_REPORT.md) | **クライアント** | API 品質評価・納品判定 |
| 🚀 [PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) | **DevOps/インフラ** | Render.com デプロイ手順 |
| ✅ [PRODUCTION_READINESS_FINAL_REPORT.md](docs/PRODUCTION_READINESS_FINAL_REPORT.md) | **プロジェクトマネージャー** | 完成度総括・リスク評価 |
| 📚 [API_ERROR_HANDLING.md](docs/API_ERROR_HANDLING.md) | **開発者** | エラーハンドリングガイド |

### **重要**: Render.com へのデプロイ前に必ず読むドキュメント
→ **[PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)**

---

## 📚 ファイル構成

```
blendy_matching/
├── src/blendy/              ← アプリ本体（Python パッケージ）
│   ├── main.py             ← FastAPI メイン（API / フォーム）
│   ├── config.py           ← 設定（環境変数対応）
│   ├── notion_client.py    ← Notion API クライアント（リトライ対応）
│   ├── matching_engine.py  ← マッチングロジック
│   └── cooperation_type_recommender.py  ← 協業タイプ推定
│
├── templates/              ← フロントエンド（HTML）
│   ├── index.html          ← ダッシュボード
│   └── register_multiactivity.html  ← 申込フォーム
│
├── tests/                  ← pytest テストスイート
│
├── docs/                   ← ドキュメント一式
│   ├── api/                ← OpenAPI spec
│   └── sales/              ← 営業資料（pptx）
│
├── scripts/                ← 運用 / 開発用スクリプト（Notion セットアップ、テストデータ投入、デプロイ等）
├── archive/                ← 旧コード・一時成果物（参照用、本番非依存）
├── backups/                ← マッチング結果バックアップ（実行時生成）
│
├── render.yaml             ← Render 設定ファイル
├── requirements.txt        ← 依存パッケージ
├── pytest.ini              ← テスト設定（pythonpath = src）
└── .env.example            ← 環境変数テンプレート
```

> 📄 各ドキュメントは [docs/](docs/) を参照してください。

### 🚀 ローカル起動

```bash
pip install -r requirements.txt
uvicorn blendy.main:app --app-dir src --reload   # → http://localhost:8000
```

> 本番（Render.com）の起動コマンドは `render.yaml` に定義済み:
> `uvicorn blendy.main:app --host 0.0.0.0 --port $PORT --app-dir src`

---

## 🏗️ インフラ / デプロイ構成

```
[ ユーザー / クライアント ]
        │  HTTPS
        ▼
┌─────────────────────────────┐        ┌──────────────────────┐
│  Render.com (Web Service)   │  API   │  Notion (実データDB)  │
│  region: singapore / free   │ ─────▶ │  メンバー / 履歴 /     │
│  uvicorn + FastAPI          │        │  結果 / 未マッチ 等    │
│  blendy.main:app            │        └──────────────────────┘
└─────────────┬───────────────┘
              │  補助的に呼び出し（シナジー加点 0〜10）
              ▼
        ┌──────────────────┐
        │ Anthropic Claude │  claude-3-5-sonnet
        └──────────────────┘
```

| 項目 | 構成 |
|------|------|
| **ホスティング** | Render.com Web Service（`region: singapore` / `plan: free`） |
| **ランタイム** | Python（`env: python`）＋ `uvicorn`（ASGI）で FastAPI を起動 |
| **デプロイ定義** | リポジトリ直下の [`render.yaml`](render.yaml)（Infrastructure as Code） |
| **ビルド** | `pip install -r requirements.txt` |
| **起動** | `uvicorn blendy.main:app --host 0.0.0.0 --port $PORT --app-dir src` |
| **データストア** | 専用DBは持たず **Notion を実DBとして利用**（複数DBをID指定でアクセス） |
| **AI 連携** | マッチングは**ルールベースのスコアリングが主軸**。Claude はシナジー加点（0〜10点）の**補助**用途で、API 失敗時はグレースフルに無視される |
| **本番URL** | `https://blendy-matching-wipa.onrender.com`（`ALLOWED_ORIGINS` に設定） |

### デプロイの流れ
1. `main` ブランチに push（または Render ダッシュボードで手動 Deploy）
2. Render が `render.yaml` を読み、`pip install` → `uvicorn` 起動
3. 環境変数・Secrets はコードに含めず **Render ダッシュボードで設定**

### 環境変数 / Secrets
`render.yaml` で定義（値は Render ダッシュボードの Environment / Secrets で設定）:

| 変数 | 用途 | 設定場所 |
|------|------|----------|
| `ENV` | `production` で認証を強制 | render.yaml |
| `LOG_LEVEL` | ログレベル | render.yaml |
| `ALLOWED_ORIGINS` | CORS 許可オリジン（カンマ区切り） | render.yaml |
| `NOTION_API_KEY` | Notion Integration Token | Secret |
| `MEMBERS_DB_ID` ほか各 `*_DB_ID` | 各 Notion DB の ID | Secret |
| `API_KEY` | ダッシュボード / 本番マッチング実行の認証キー | ダッシュボードで要設定 |
| `CLAUDE_API_KEY` | Claude シナジー加点用 | ダッシュボードで要設定 |

### 認証モデル
- **申込フォーム系**: `API_KEY` 未設定なら認証スキップ（クライアントが常時フォーム利用可）。設定時は `X-API-Key` を検証
- **ダッシュボード / マッチング実行**: 常に `X-API-Key` 必須（未設定だとサーバーエラー）

### ⚠️ 運用上の注意
- **`render.yaml` に `CLAUDE_API_KEY` / `API_KEY` の定義がない** → これらは Render ダッシュボードで手動設定が必要。`CLAUDE_API_KEY` 未設定だと Claude のシナジー加点は無効化される（マッチング自体はルールベースで動作）
- **free プランはファイルシステムが揮発性** → `matching_engine.save_backup()` が書き出す `backups/` は再起動・再デプロイで消失する。永続化が必要なら Notion 側へ保存するか有料プラン＋ディスクを検討
- **free プランはアイドルでスリープ** → 初回アクセス時にコールドスタートの遅延が発生する


### **開発環境（ローカル）**

```bash
# サーバー起動
uvicorn blendy.main:app --app-dir src --reload
# → http://localhost:8000
```

| エンドポイント | メソッド | 認証 | 説明 |
|-------------|---------|------|------|
| `/api/stats` | GET | 不要 | 統計情報取得 |
| `/api/register` | POST | 不要 | メンバー登録 |
| `/api/run-matching` | POST | 開発環境では不要 | マッチング実行 |
| `/api/results` | GET | 不要 | マッチング結果取得 |
| `/docs` | GET | 不要 | Swagger UI（対話的テスト） |

### **本番環境（Render.com）**

> ⚠️ **重要**: 本番環境では `/api/run-matching` に **X-API-Key ヘッダーが必須**です

```bash
# 本番環境の場合
curl -X POST "https://blendy-matching.onrender.com/api/run-matching" \
  -H "X-API-Key: your-production-api-key"
```

詳細は → **[API_ERROR_HANDLING.md](docs/API_ERROR_HANDLING.md)** を参照

---

## 🎯 開発環境での使い方（3ステップ）

### ステップ 1️⃣ : 起動

**最も簡単な方法:**

Windows なら → `quick_share.cmd` をダブルクリック

その他：
```bash
python scripts/deploy.py
```

### ステップ 2️⃣ : URL を確認

ターミナルに表示される URL をコピー（例）:
```
https://abc123xyz.ngrok.io
```

または http://localhost:4040 で確認

### ステップ 3️⃣ : 外部ユーザーに送信

フォーム URL を共有：
```
https://abc123xyz.ngrok.io/register
```

---

## 🔧 初回セットアップ

```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. ngrok をインストール（外部公開の場合）
# https://ngrok.com/download

# 3. ngrok を認証
ngrok config add-authtoken YOUR_TOKEN
```

---

## 📖 詳しい説明

| ガイド | 用途 |
|--------|------|
| 📋 **SHARING_CHECKLIST.md** | ✅ 共有前に必ずチェック |
| 📋 **DEPLOY_GUIDE.md** | 📚 詳細なトラブルシューティング |

---

## 🌐 アクセス URL

| 機能 | URL |
|------|-----|
| 📝 申込フォーム | `https://xxx.ngrok.io/register` |
| 📊 ダッシュボード | `https://xxx.ngrok.io/` |
| 🔍 ngrok コンソール | `http://localhost:4040` |
| 💾 Notion DB | プロジェクト設定の URL |

---

## 🆘 よくあるエラー

| エラー | 対応 |
|--------|------|
| `ポート 8001 が既に使用中` | スクリプトが自動で処理 |
| `ngrok が見つかりません` | https://ngrok.com/download |
| `フォーム送信後にエラー` | SHARING_CHECKLIST.md 参照 |
| `Notion にデータ保存されない` | notion_client.py の設定確認 |

---

## 💡 ヒント

- **ローカルのみでテスト:** `http://localhost:8001/register`
- **トラフィック監視:** `http://localhost:4040` (ngrok 実行中)
- **24時間後に URL が切れます** → 再度デプロイして新 URL 発行
- **複数ユーザーが同時アクセス OK**

---

## 📱 動作確認フロー

```
1. quick_share.cmd 実行
   ↓
2. ngrok URL をコピー
   ↓
3. テスト送信: https://xxx.ngrok.io/register
   ↓
4. ダッシュボードで確認: https://xxx.ngrok.io/
   ↓
5. Notion DB で確認
   ↓
6. 外部ユーザーに URL を共有
```

---

## 🔒 セキュリティ注意

- ngrok URL は **誰でもアクセス可能** → 信頼できる人のみに共有
- **24時間で自動切断** → 安全
- **Notion API キー** は秘密に保つ

---

## 📞 トラブル時

1. **SHARING_CHECKLIST.md** をチェック
2. **DEPLOY_GUIDE.md** のトラブルシューティング参照
3. ターミナルのエラーメッセージを確認
4. Notion API キー設定を確認

---

## ✨ 最後に確認すること

共有する前に、必ず実行してください:

```bash
# 1. テスト送信を完了したか？
http://localhost:8001/register

# 2. Notion に記録されたか確認したか？
ダッシュボード → 統計を確認

# 3. 外部 URL をコピーしたか？
ngrok コンソール (localhost:4040) で確認
```

---

**準備完了したら → 外部ユーザーに URL を送信してください！** 🎉
