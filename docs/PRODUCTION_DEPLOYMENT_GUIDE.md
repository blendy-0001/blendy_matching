# 本番環境デプロイメントガイド
## Blendy Matching API - Render.com デプロイ手順

**作成日**: 2026-05-25  
**対象**: blendy_matching API  
**デプロイ先**: Render.com  
**ステータス**: ✅ 本番デプロイ準備完了

---

## 📋 デプロイ前チェックリスト

### ✅ コード・セキュリティの確認

- [x] `.env` ファイルが `.gitignore` に含まれているか
- [x] API キーがハードコードされていないか
- [x] 環境変数がすべて `os.getenv()` で読み込まれているか
- [x] `requirements.txt` に必要な全依存ファイルが含まれているか
  - ✅ `tenacity==8.2.3` (リトライロジック)
  - ✅ `fastapi==0.115.0`
  - ✅ `uvicorn==0.30.6`
  - ✅ `requests==2.32.3`
  - ✅ その他全て

### ✅ セキュリティ機能の確認

| 機能 | 実装 | 検証 |
|------|------|------|
| **API キー認証** | ✅ main.py: `verify_api_key()` | 本番環境で必須 |
| **CORS 設定** | ✅ main.py: `CORSMiddleware` | ALLOWED_ORIGINS 環境変数で制御 |
| **セキュリティヘッダー** | ✅ main.py: `add_security_headers()` | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection |
| **ログレベル制御** | ✅ config.py: `LOG_LEVEL` | 本番は INFO 以上 |
| **エラー詳細隠蔽** | ✅ main.py: エラーハンドラー | ユーザーには安全なメッセージのみ |

### ✅ エラーハンドリングの確認

| 項目 | 実装 | 詳細 |
|------|------|------|
| **Notion API リトライ** | ✅ notion_client.py | `@retry` デコレーター、指数バックオフ (3回まで) |
| **タイムアウト設定** | ✅ notion_client.py | 全 API 呼び出しに `timeout=10` |
| **例外ハンドリング** | ✅ main.py | try/except でエラーを適切に捕捉 |
| **バックアップエラー処理** | ✅ main.py: `_run_matching_task()` | エラーでもマッチング結果は Notion に保存 |

### ✅ テスト・ドキュメントの確認

- [x] API 評価レポート作成済み (API_EVALUATION_REPORT.md)
- [x] テストスイート実装済み (tests/ ディレクトリ)
  - ✅ `test_scoring.py` - スコアリングロジック
  - ✅ `test_name_normalization.py` - 名前正規化
  - ✅ `test_matching_history.py` - マッチング履歴
  - ✅ `test_balanced_selection.py` - バランス選定
- [x] OpenAPI/Swagger ドキュメント自動生成 (FastAPI)

---

## 🚀 デプロイ手順

### **ステップ 1: コードの準備確認**

```bash
# コードをクローン・プッシュ
cd blendy_matching
git status                    # uncommitted changes を確認
git add .                     # すべての変更を追加（.env は除外されている）
git commit -m "Production readiness: Phase 1-4 implementation complete"
git push origin main          # リモートリポジトリにプッシュ
```

**確認項目：**
- `.env` ファイルが git に含まれていないこと
- `requirements.txt` が最新であること
- `render.yaml` が存在すること

### **ステップ 2: Render.com ダッシュボードで環境変数を設定**

Render.com ダッシュボード → サービス設定 → Environment

#### **標準環境変数（明示設定）:**

| キー | 値 | 説明 |
|------|-----|------|
| `ENV` | `production` | 本番環境モード（API キー認証を強制） |
| `LOG_LEVEL` | `INFO` | ログレベル（本番は INFO 推奨） |
| `ALLOWED_ORIGINS` | `https://blendy-matching.onrender.com` | CORS 許可オリジン（実際のドメインに置き換え） |

#### **Secrets で設定（機密情報）:**

ダッシュボード → Environment → **Secrets** セクションで以下を追加：

| キー | 値 | 取得方法 |
|------|-----|---------|
| `NOTION_API_KEY` | `ntn_...` | Notion API 設定ページから取得 |
| `CLAUDE_API_KEY` | `sk-ant-...` | Anthropic Console から取得 |
| `API_KEY` | ランダムな強力なキー | `openssl rand -hex 32` で生成推奨 |
| `MEMBERS_DB_ID` | UUID | Notion ページ URL から抽出 |
| `MATCHING_HISTORY_DB_ID` | UUID | Notion ページ URL から抽出 |
| `MATCHING_RESULTS_DB_ID` | UUID | Notion ページ URL から抽出 |
| `UNMATCHED_MEMBERS_DB_ID` | UUID | Notion ページ URL から抽出 |

**Secrets の設定方法:**
1. Render ダッシュボード → Environment タブ
2. "Add Secret" をクリック
3. キー・値を入力して保存

### **ステップ 3: デプロイの実行**

**方法 A: Render ダッシュボード（推奨）**
1. Render.com ダッシュボードにログイン
2. 対象サービス (blendy-matching) を選択
3. "Deploy latest commit" をクリック
4. デプロイログを確認（3-5分待機）

**方法 B: コマンドライン**
```bash
# Render CLI でデプロイ
render deploy --service blendy-matching
```

### **ステップ 4: デプロイ後の検証**

#### **4-1: サーバー起動確認**
```bash
# Render ダッシュボード → Logs タブで以下を確認
# "Uvicorn running on http://0.0.0.0:10000"
```

#### **4-2: エンドポイント動作確認**

デプロイ後、実際の本番ドメインで検証：

```bash
# API キーを取得（Render Secrets から確認）
API_KEY="your-production-api-key"
DOMAIN="https://blendy-matching.onrender.com"

# 1. GET /api/stats （認証不要）
curl -s "${DOMAIN}/api/stats" | jq .

# 2. POST /api/run-matching （本番環境では API キー必須）
curl -X POST "${DOMAIN}/api/run-matching" \
  -H "X-API-Key: ${API_KEY}" | jq .

# 3. GET /api/results
curl -s "${DOMAIN}/api/results" | jq .

# 4. Swagger UI にアクセス
curl -s "${DOMAIN}/docs"
```

#### **4-3: エラーレスポンス検証**

```bash
# 無効な API キーでテスト（403 Forbidden を返すはず）
curl -X POST "https://blendy-matching.onrender.com/api/run-matching" \
  -H "X-API-Key: invalid-key"
# → {"detail":"Invalid or missing API key"} (status 403)

# API キーなしでテスト（422 を返すはず）
curl -X POST "https://blendy-matching.onrender.com/api/run-matching"
# → {"detail":"X-API-Key header is required in production mode"} (status 422)
```

---

## 📊 本番環境の監視設定

### **Render.com での監視**

1. **ダッシュボード → Notifications**
   - エラーログメール通知を有効化
   - Uptime monitoring を有効化

2. **ダッシュボード → Logs**
   - ERROR/CRITICAL レベルのログを定期確認
   - Notion API エラー率の監視

### **推奨される定期チェック**

```
【毎日】
- エラーログに CRITICAL なし
- Notion API のタイムアウトなし

【毎週】
- マッチング処理の成功率
- 平均応答時間
- CPU/メモリ使用率

【毎月】
- Notion DB 容量確認
- バックアップの実施
- セキュリティアップデート確認
```

---

## 🔐 本番環境セキュリティのベストプラクティス

### **API キー管理**
- ✅ API キーは絶対に git に含めない
- ✅ Render Secrets で安全に管理
- ✅ 3ヶ月ごとにキーのローテーション推奨

### **CORS 設定**
- ✅ `ALLOWED_ORIGINS` は実際のドメインに限定
- ✅ ワイルドカード（`*`）は使用禁止
- ✅ クライアント追加時に環境変数を更新

### **ログ設定**
- ✅ 本番環境は `LOG_LEVEL=INFO` 以上
- ✅ デバッグ情報（DEBUG）は本番に出力しない
- ✅ トレーサーバックは内部ログのみ

### **HTTPS/SSL**
- ✅ Render.com は自動的に HTTPS を提供
- ✅ HSTS ヘッダーで強制（実装済み）

---

## ⚠️ よくあるトラブルシューティング

### **問題 1: デプロイ後 500 Internal Server Error**

**原因：** 環境変数が未設定

**解決策：**
```bash
# Render ダッシュボード → Logs を確認
# "KeyError: 'NOTION_API_KEY'" などが表示されていないか確認
# → Secrets に API キーが設定されているか確認
```

### **問題 2: API キー認証が機能しない**

**原因：** `ENV=production` が未設定

**解決策：**
```bash
# .env ファイル確認（ローカルの場合）
cat .env | grep ENV

# Render ダッシュボード → Environment で ENV=production が設定されているか確認
```

### **問題 3: CORS エラー**

**原因：** `ALLOWED_ORIGINS` が正しく設定されていない

**解決策：**
```bash
# 実際のクライアント URL を ALLOWED_ORIGINS に追加
# 複数オリジンの場合：カンマ区切り
# ALLOWED_ORIGINS=https://domain1.com,https://domain2.com
```

### **問題 4: Notion API タイムアウト**

**原因：** Notion API が一時的に遅い、またはリトライが枯渇

**対応：** 
- リトライロジックが自動的に 3 回まで試行
- タイムアウトは 10 秒に設定
- ユーザーには「しばらくお待ちください」メッセージを表示

---

## ✅ デプロイ完了確認チェックリスト

```
デプロイ前：
- [ ] git push で全コミットが送信されたか
- [ ] render.yaml が正しく設定されているか

デプロイ中：
- [ ] デプロイログにエラーがないか
- [ ] "Build succeeded" メッセージが表示されているか
- [ ] サーバー起動に 3-5 分要した

デプロイ後：
- [ ] Swagger UI にアクセス可能（https://domain/docs）
- [ ] GET /api/stats で 200 応答
- [ ] POST /api/run-matching で認証が機能（有効キー: 200, 無効: 403）
- [ ] エラーログに CRITICAL がない
- [ ] マッチング処理が正常に実行されたか
```

---

## 📞 サポート情報

### **デプロイ中の問題**
- **Render Status**: https://status.render.com
- **Render Documentation**: https://render.com/docs

### **API 関連**
- **Notion API**: https://developers.notion.com
- **FastAPI**: https://fastapi.tiangolo.com
- **Anthropic**: https://docs.anthropic.com

---

## 🎯 次のステップ

### **即座（本日）**
1. ✅ コード最終確認
2. ✅ Render.com 環境変数設定
3. ✅ デプロイ実行

### **24時間以内**
1. 本番 API の動作確認
2. クライアント様にテスト用 API キーを配布
3. 簡単な操作ガイドを提供

### **1週間以内**
1. Notion API 統合状況の監視
2. エラーログの確認
3. 本番環境の安定性を検証

### **今後の改善**（将来バージョン）
1. Webhook 機能（マッチング完了時自動通知）
2. レート制限（API 呼び出し頻度制御）
3. より詳細なダッシュボード
4. メール通知機能

---

**最終判定：✅ 本番デプロイ準備完了**

**推奨スケジュール：**
- **本日**: 環境変数設定
- **明日**: Render.com にデプロイ
- **明後日**: 本番テストと最終検証
- **1週間後**: クライアント様への提供開始

---

**作成者**: Claude Code Agent  
**最終更新**: 2026-05-25 UTC  
**ステータス**: ✅ 本番環境対応完了
