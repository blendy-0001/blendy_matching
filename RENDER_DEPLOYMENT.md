# Render.com へのデプロイメント手順

協業マッチングシステムを Render.com に本番デプロイするための詳細な手順です。

---

## Step 1: Render.com アカウント準備

### 1.1 Render.com にサインアップ
1. [Render.com](https://render.com) にアクセス
2. GitHub アカウントで サインアップ
3. リポジトリへのアクセス権限を付与

### 1.2 GitHub リポジトリの確認
```bash
# リポジトリが公開されているか確認
git remote -v
# origin: https://github.com/...../blendy_matching.git
```

---

## Step 2: Render.com でサービスを作成

### 2.1 新規 Web Service を作成
1. Render.com ダッシュボードにログイン
2. **New +** → **Web Service**
3. GitHub リポジトリを選択（`blendy_matching`）
4. デプロイ設定：
   - **Name**: `blendy-matching`
   - **Environment**: `Python 3`
   - **Region**: `Singapore` または `Tokyo`
   - **Branch**: `main` または `feature/production-ready`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free` (無料) または `Starter` (本運用向け)

### 2.2 デプロイを開始
- **Create Web Service** をクリック
- ビルドが開始される（5-10 分）
- ビルド完了まで待機

---

## Step 3: 環境変数を設定

### 3.1 Secrets を設定（秘密情報）

Render.com ダッシュボード → Web Service → **Environment** → **Secret Files**

以下のシークレットを追加：

| Secret 名 | 値 | 説明 |
|-----------|-----|------|
| `NOTION_API_KEY` | `secret_xxxxx...` | Notion Integration Token |
| `CLAUDE_API_KEY` | `sk-ant-xxxxx...` | Anthropic Claude API Key |
| `API_KEY` | `[安全なランダムキー]` | API 認証キー |
| `MEMBERS_DB_ID` | `517b9ae4-...` | Notion メンバーリスト DB ID |
| `MATCHING_HISTORY_DB_ID` | `f650ca34-...` | Notion マッチング履歴 DB ID |
| `MATCHING_RESULTS_DB_ID` | `968cbe70-...` | Notion マッチング結果 DB ID |
| `UNMATCHED_MEMBERS_DB_ID` | `b663ca20-...` | Notion 未マッチメンバー DB ID |

#### API_KEY の生成方法
```bash
# ローカルで安全なランダムキーを生成
openssl rand -hex 32
# 出力例: a7f3c2d8e9b1f4a6c8e2d7f3a5b8c1e4d9f2a5b7c8e1d3f5a7b9c2e4f6a8b

# または Python で
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.2 環境変数を設定（公開情報）

**Environment** → **Environment Variables**

| Key | Value |
|-----|-------|
| `ENV` | `production` |
| `LOG_LEVEL` | `INFO` |
| `ALLOWED_ORIGINS` | `https://blendy-matching.onrender.com` |

### 3.3 環境変数の確認
```
✓ ENV=production
✓ LOG_LEVEL=INFO
✓ ALLOWED_ORIGINS=https://blendy-matching.onrender.com
✓ [Secrets] NOTION_API_KEY
✓ [Secrets] CLAUDE_API_KEY
✓ [Secrets] API_KEY
✓ [Secrets] MEMBERS_DB_ID
✓ [Secrets] MATCHING_HISTORY_DB_ID
✓ [Secrets] MATCHING_RESULTS_DB_ID
✓ [Secrets] UNMATCHED_MEMBERS_DB_ID
```

---

## Step 4: Notion インテグレーション権限の確認

### 4.1 Notion インテグレーション確認
1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「Blendy Matching」インテグレーションを選択
3. **Capabilities** を確認：
   - ✅ Read content
   - ✅ Create content
   - ✅ Update content
   - ✅ Delete content

### 4.2 DB へのアクセス権限設定
各 Notion DB について：
1. DB を開く
2. **Share** → インテグレーションを選択
3. 権限を確認（最小: Read, Create; 推奨: Read, Create, Update）

---

## Step 5: デプロイ検証

### 5.1 デプロイ状態確認
Render.com ダッシュボード → **Logs**
```
✓ Build started
✓ Successfully built Python dependencies
✓ Starting service on port 10000
✓ Uvicorn running on 0.0.0.0:10000
```

### 5.2 本番環境への接続テスト
```bash
# ダッシュボード確認
curl -s https://blendy-matching.onrender.com/ | head -20

# API 統計確認
curl -s https://blendy-matching.onrender.com/api/stats | jq .

# API 認証テスト（403 が返るはず）
curl -s -X POST https://blendy-matching.onrender.com/api/run-matching | jq .

# 正しい API キーでテスト
curl -s -X POST https://blendy-matching.onrender.com/api/run-matching \
  -H "X-API-Key: [YOUR_API_KEY]" | jq .
```

### 5.3 ダッシュボード動作確認
1. https://blendy-matching.onrender.com を開く
2. ダッシュボード表示確認
3. マッチング実行ボタンをテスト（認証キー必須）

---

## Step 6: 監視・アラート設定

### 6.1 Render.com 監視
1. **Notifications** → **Email Alerts** 有効化
   - ✅ Build failed
   - ✅ Deploy failed
   - ✅ Instance crashed

2. **Health Checks** 設定（オプション）
   - Endpoint: `https://blendy-matching.onrender.com/`
   - Interval: 5 minutes

### 6.2 ログ監視の計画
- 毎日午前にログを確認する
- ERROR/CRITICAL は即座に対応

---

## Step 7: 本番運用チェックリスト

### 初回デプロイ直後
- [ ] ダッシュボード (/) に アクセス可能
- [ ] API ドキュメント (/docs) に アクセス可能
- [ ] 登録フォーム (/register) が動作
- [ ] マッチング実行が認証で保護されている
- [ ] Notion DB に データが記録されている

### 定期確認（週 1 回）
- [ ] エラーログ確認
- [ ] マッチング成功率確認
- [ ] API レスポンスタイム確認（< 5秒）
- [ ] バックアップ確認

### 定期メンテナンス（月 1 回）
- [ ] API キー交換（セキュリティ向上）
- [ ] ログアーカイブ
- [ ] Notion DB スナップショット

---

## トラブルシューティング

### ビルドが失敗する
```
Error: Failed to install dependencies
```
**対応**: requirements.txt が正しいか確認
```bash
pip install -r requirements.txt  # ローカルで確認
```

### サービスがクラッシュする
```
Log: [ERROR] ModuleNotFoundError: No module named 'notion_client'
```
**対応**: 
1. requirements.txt に すべての依存が含まれているか確認
2. Render.com でビルドを再実行 (Redeploy)

### Notion API エラー
```
Log: [ERROR] Notion API error: 403 Unauthorized
```
**対応**: 
1. NOTION_API_KEY が正しいか確認
2. インテグレーション権限を確認
3. DB へのアクセス権限を再確認

### API 認証が機能しない
```
Log: [DEBUG] Development mode: API key verification skipped
```
**対応**: ENV=production が設定されているか確認
```bash
# Render.com ダッシュボール → Environment Variables
# ENV = production に設定されているはず
```

---

## 本番環境 URL

- **ダッシュボード**: https://blendy-matching.onrender.com
- **登録フォーム**: https://blendy-matching.onrender.com/register
- **API ドキュメント**: https://blendy-matching.onrender.com/docs
- **API 統計**: https://blendy-matching.onrender.com/api/stats

---

## セキュリティベストプラクティス

1. **API_KEY は定期的に変更**（月 1 回）
   ```bash
   # 新キーを生成
   openssl rand -hex 32
   # Render.com Secrets で更新
   ```

2. **ログ内容を監視**
   - 不正なアクセス試行がないか確認
   - Notion API エラー率を監視

3. **バックアップを定期実施**
   - Notion DB のスナップショットを取得（Team Plan 推奨）
   - ローカルバックアップを GitHub に定期コミット

---

## 次のステップ

- [ ] Render.com での初回デプロイ完了
- [ ] 本番環境での E2E テスト実施
- [ ] クライアント向けドキュメント準備
- [ ] 本番環境 URL の共有
