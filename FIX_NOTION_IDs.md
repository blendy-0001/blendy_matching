# Notion Database ID 設定ガイド

## 問題
サーバーが Notion API から 404 エラーを返しています。
```
https://api.notion.com/v1/data_sources/31735db8e7474a4c9e3500ab9b81f49a/query HTTP/1.1" 404
```

## 原因
- `.env` の `MEMBERS_DB_ID=31735db8e7474a4c9e3500ab9b81f49a` はハイフンなし形式（database_id）
- コードは `/data_sources/{id}/query` エンドポイントを使用（data_source_id が必要）
- Notion API v2026-03-11では、データベースクエリには data_source_id（UUID形式）が必要

## 解決方法

### 1. Notion ダッシュボードから正しい ID を取得

**メンバーリスト DB の場合：**
1. Notion ダッシュボードで「メンバーリスト2」を開く
2. URL を確認：`https://www.notion.so/xxxxx?v=yyyyyyyy`
   - または Properties パネルから Database ID を確認
3. **data_source_id** (UUID形式: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) を探す

### 2. `.env` を更新

**現在：**
```
MEMBERS_DB_ID=31735db8e7474a4c9e3500ab9b81f49a
ACTIVITIES_DB_ID=4655e4e3-89f0-4852-b999-2801483bd8b5
```

**正しい形式（すべてハイフン形式）：**
```
MEMBERS_DB_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ACTIVITIES_DB_ID=4655e4e3-89f0-4852-b999-2801483bd8b5
MATCHING_HISTORY_DB_ID=e489e92d-fffc-4ae1-b2d1-0784a57adbfd
MATCHING_RESULTS_DB_ID=2e6baab3-4b6c-465d-af11-95e049e2ae9a
UNMATCHED_MEMBERS_DB_ID=49e6f31e-5bd6-41aa-8cc6-b2d24a61502f
```

### 3. サーバーを再起動

```bash
# Kill existing process
Get-Process -Name python | Stop-Process -Force

# Restart server
python main.py
```

## デバッグ方法

サーバーが起動したら、以下でエラーログを確認：
```bash
Get-Content "server_error.log" -Tail 50
```

正常に動作すると、以下のメッセージが表示されます：
```
[DEBUG] Attempting to query MEMBERS_DB with ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

**注：** ID に迷ったら、Notion ワークスペースの管理画面で「メンバーリスト」を右クリック → プロパティで確認できます。
