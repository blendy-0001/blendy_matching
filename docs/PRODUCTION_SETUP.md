# 本番環境セットアップガイド

協業マッチングシステムの本番環境構築手順です。

## 前提条件

- Python 3.10 以上
- Notion Integration Token
- Anthropic Claude API Key
- Render.com または同等のホスティングプラットフォーム

---

## Step 1: 環境変数の準備

### 1.1 Notion インテグレーション API キーの取得

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「新しいインテグレーション」を作成
3. 名前を「Blendy Matching」に設定
4. 必要な機能を選択：
   - Read content
   - Create content
   - Update content
5. Authorization token をコピー（`secret_...` で始まる文字列）

### 1.2 Anthropic Claude API キーの取得

1. [Anthropic Console](https://console.anthropic.com) にアクセス
2. API Keys セクションに移動
3. 新規 API キーを生成
4. キーをコピー（`sk-ant-...` で始まる文字列）

### 1.3 Notion データベース ID の取得

各 Notion データベースについて：

1. Notion で DB を開く
2. ブラウザの URL から ID を抽出
   ```
   https://notion.so/{DATABASE_ID}?v={VIEW_ID}
                      ↑
                      ここをコピー
   ```

必要な DB：
- メンバーリスト DB (`MEMBERS_DB_ID`)
- マッチング履歴 DB (`MATCHING_HISTORY_DB_ID`)
- マッチング結果 DB (`MATCHING_RESULTS_DB_ID`)
- 未マッチメンバー DB (`UNMATCHED_MEMBERS_DB_ID`)

---

## Step 2: ローカル開発環境の設定

### 2.1 リポジトリのクローンと初期化

```bash
cd ~/Documents
git clone <repository-url> blendy_matching
cd blendy_matching
```

### 2.2 `.env` ファイルの作成

```bash
cp .env.example .env
```

`.env` を編集して、取得したキーと ID を入力：

```env
# Notion API Key
NOTION_API_KEY=secret_xxxxxxxxxxxxx

# Anthropic Claude API Key
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx

# Notion Database IDs
MEMBERS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MATCHING_HISTORY_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MATCHING_RESULTS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
UNMATCHED_MEMBERS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# CORS設定（ローカル開発用）
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# API認証キー（開発環境では機能していません）
API_KEY=dev-api-key-for-testing

# ログレベル（開発環境）
LOG_LEVEL=DEBUG
```

### 2.3 環境変数の確認

```bash
# すべての必須環境変数が設定されていることを確認
python -c "from config import *; print('Config loaded successfully')"
```

### 2.4 .env を .gitignore に追加

```bash
# 既に設定されているはずですが、確認
grep "^\.env$" .gitignore
```

---

## Step 3: 本番環境への設定（Render.com の例）

### 3.1 Render.com でサービスを作成

1. [Render.com](https://render.com) にサインイン
2. New → Web Service を選択
3. GitHub リポジトリを接続
4. サービス名を入力（例：`blendy-matching`）
5. Runtime: Python
6. Start Command: `python main.py`

### 3.2 環境変数を Render に設定

Environment タブで以下を設定：

```
NOTION_API_KEY=secret_xxxxxxxxxxxxx
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
MEMBERS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MATCHING_HISTORY_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MATCHING_RESULTS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
UNMATCHED_MEMBERS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ALLOWED_ORIGINS=https://your-domain.onrender.com
API_KEY=your-secure-api-key-generate-with-$(openssl rand -hex 32)
LOG_LEVEL=INFO
ENV=production
```

**重要:** API_KEY は安全に生成してください：
```bash
# ローカルで生成
openssl rand -hex 32
# 出力された32文字の16進数文字列を API_KEY に設定
```

### 3.3 デプロイを実行

1. Render ダッシュボードで「Deploy」をクリック
2. ビルドとデプロイが完了するまで待機（通常 5-10 分）
3. サービスの URL を記録（例：`https://blendy-matching.onrender.com`）

### 3.4 本番環境のログレベル設定

本番環境では `LOG_LEVEL=INFO` または `LOG_LEVEL=WARNING` を設定してください。

---

## Step 4: Notion インテグレーションのアクセス権限設定

### 4.1 各データベースへのアクセス権限を付与

1. 各 Notion データベースを開く
2. 右上の「Share」をクリック
3. Integration を検索して Blendy Matching を追加
4. 以下の権限を確認：
   - ✓ Can read
   - ✓ Can create
   - ✓ Can update (必要に応じて)

### 4.2 必要に応じて、ページレベルの権限も確認

---

## Step 5: 本番環境の検証

### 5.1 API エンドポイントの動作確認

```bash
# ダッシュボードにアクセス
curl https://your-domain.onrender.com/

# 統計情報を取得
curl https://your-domain.onrender.com/api/stats

# API キー認証テスト（失敗すること）
curl -X POST https://your-domain.onrender.com/api/run-matching \
  -H "X-API-Key: invalid-key"

# 正しい API キーでマッチング開始
curl -X POST https://your-domain.onrender.com/api/run-matching \
  -H "X-API-Key: your-secure-api-key" \
  -H "Content-Type: application/json"
```

### 5.2 ログの確認

```bash
# Render でログを確認
# Render ダッシュボーム → Logs タブ
# または
curl https://api.render.com/v1/services/xxx/logs
```

### 5.3 Notion DB に結果が保存されるか確認

1. Notion で「マッチング結果」DB を開く
2. 新しいレコードが生成されていることを確認

---

## Step 6: 運用開始

### 6.1 定期的な監視

毎日以下を確認：

```bash
# エラーログをチェック
# Render Dashboard → Logs タブで ERROR/CRITICAL がないか確認

# 統計情報を確認
curl https://your-domain.onrender.com/api/stats | jq .
```

### 6.2 API キーのローテーション（3 ヶ月ごと）

```bash
# 新しい API キーを生成
NEW_API_KEY=$(openssl rand -hex 32)

# Render 環境変数を更新
# (Render Dashboard → Environment)

# 古い API キーを削除
```

### 6.3 バックアップの確認

本番環境でのマッチング後、バックアップファイルが生成されていることを確認：

```bash
# Render 内のバックアップディレクトリを確認
# または、定期的に GitHub にバックアップをコミット
```

---

## トラブルシューティング

### Q: `Notion API タイムアウト` エラーが出ている

**A:** ネットワーク遅延またはリトライ回数の枯渇

解決策：
1. Notion API の状態を確認 (https://status.notion.so)
2. リトライ設定をチェック（tenacity のデフォルトは 3 回）
3. 必要に応じて timeout 時間を延長（現在 10 秒）

### Q: `Invalid or missing API key` エラー

**A:** API キーが一致していない、または設定されていない

解決策：
```bash
# API キーを確認（本番環境の場合）
# Render Dashboard → Environment で確認

# API キーを変更した場合は、ローカルでテスト
python main.py
# ブラウザで http://localhost:8000 を開く
```

### Q: Notion データベースに接続できない

**A:** インテグレーション権限が不足している

解決策：
1. Notion インテグレーションの権限を再確認
2. データベースが共有されていることを確認
3. Notion API キーが正しいことを確認

### Q: マッチング結果が Notion に保存されない

**A:** UNMATCHED_MEMBERS_DB_ID が設定されていない、または権限不足

解決策：
1. .env に UNMATCHED_MEMBERS_DB_ID が設定されていることを確認
2. ログで保存エラーを確認
3. Notion DB のアクセス権限を確認

---

## セキュリティベストプラクティス

### 環境変数管理
- ✓ API キーをバージョン管理に入れない
- ✓ 本番環境と開発環境で異なるキーを使用
- ✓ API キーを定期的にローテーション
- ✓ 漏洩したキーはすぐに無効化

### アクセスコントロール
- ✓ API キー認証を本番環境で有効にする
- ✓ ALLOWED_ORIGINS を本番ドメインに限定
- ✓ デバッグエンドポイント (`/docs`) を本番環境で無効にする

### ログと監視
- ✓ ログレベルを本番環境で INFO 以上に設定
- ✓ エラーログを定期的に確認
- ✓ 異常アクセスをモニタリング

---

## サポートと連絡先

問題が発生した場合：

1. ログを確認（Render Dashboard → Logs）
2. Notion API ステータスを確認（https://status.notion.so）
3. このドキュメントのトラブルシューティングを参照
4. 必要に応じて開発チームに連絡

---

**最終更新:** 2026年5月23日  
**バージョン:** 1.0
