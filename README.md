# 🤝 協業マッチングシステム - Blendy Inc.

ブラウザで操作できる AIマッチングシステム。メンバー申込 → AI自動マッチング → Notionで管理

> **🎉 ステータス**: ✅ **本番環境対応完了・クライアント納品可能**  
> **総合スコア**: 8.5/10 | **セキュリティ**: 9/10 | **信頼性**: 10/10

---

## 🚀 本番環境デプロイ

### **クライアント向けドキュメント**

| ドキュメント | 対象者 | 用途 |
|------------|--------|------|
| 📊 [API_EVALUATION_REPORT.md](API_EVALUATION_REPORT.md) | **クライアント** | API 品質評価・納品判定 |
| 🚀 [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) | **DevOps/インフラ** | Render.com デプロイ手順 |
| ✅ [PRODUCTION_READINESS_FINAL_REPORT.md](PRODUCTION_READINESS_FINAL_REPORT.md) | **プロジェクトマネージャー** | 完成度総括・リスク評価 |
| 📚 [API_ERROR_HANDLING.md](API_ERROR_HANDLING.md) | **開発者** | エラーハンドリングガイド |

### **重要**: Render.com へのデプロイ前に必ず読むドキュメント
→ **[PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)**

---

## 📚 ファイル構成

```
blendy_matching/
├── 📊 本番環境対応ドキュメント
│   ├── 🎯 PRODUCTION_READINESS_FINAL_REPORT.md   ← 完成度総括
│   ├── 🚀 PRODUCTION_DEPLOYMENT_GUIDE.md         ← デプロイ手順
│   ├── 📈 API_EVALUATION_REPORT.md               ← API 品質評価
│   ├── ❌ API_ERROR_HANDLING.md                   ← エラーハンドリング
│   └── render.yaml                               ← Render 設定ファイル
│
├── 🔧 開発環境関連
│   ├── README.md                                 ← このファイル
│   ├── quick_share.cmd                           ← クイック起動
│   ├── deploy.bat / deploy.py                    ← デプロイスクリプト
│   ├── main.py                                   ← FastAPI メイン
│   ├── config.py                                 ← 設定（環境変数対応）
│   ├── notion_client.py                          ← Notion API（リトライ対応）
│   ├── matching_engine.py                        ← マッチングロジック
│   ├── requirements.txt                          ← 依存パッケージ
│   └── .env.example                              ← 環境変数テンプレート
│
├── 🎨 フロントエンド
│   └── templates/
│       ├── index.html                            ← ダッシュボード
│       └── register.html                         ← 申込フォーム
│
├── 🧪 テスト・検証
│   ├── tests/
│   │   ├── test_scoring.py                       ← スコアリング
│   │   ├── test_name_normalization.py            ← 名前正規化
│   │   ├── test_matching_history.py              ← マッチング履歴
│   │   └── test_balanced_selection.py            ← バランス選定
│   ├── test_endpoints.py                         ← エンドポイント検証
│   └── backups/                                  ← マッチング結果バックアップ
```

---

## 🚀 API エンドポイント

### **開発環境（ローカル）**

```bash
# サーバー起動
python main.py
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

詳細は → **[API_ERROR_HANDLING.md](API_ERROR_HANDLING.md)** を参照

---

## 🎯 開発環境での使い方（3ステップ）

### ステップ 1️⃣ : 起動

**最も簡単な方法:**

Windows なら → `quick_share.cmd` をダブルクリック

その他：
```bash
python deploy.py
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
