# Notion API ID 診断と修正ガイド

## 問題の詳細

`create_member()` 関数が Notion API に失敗している理由:

### 現在の状態
```
MEMBERS_DB_ID = 51c2fae4-ac36-4d51-bced-8a4b203b5768
               ↓ 
               これは data_source_id (クエリ用)
```

### エラー
```
404: Could not find database with ID: 51c2fae4-ac36...
```

### 理由
- ✅ `GET /data_sources/{id}/query` には有効
- ❌ `POST /pages` には無効（database_id が必要）

---

## 修正方法

### Step 1: 正しい DATABASE_ID を取得

各データベースについて、Notion ブラウザで以下を確認:

1. **MEMBERS データベース** を開く
2. ブラウザのアドレスバーを確認

**パターン A:** 新しい Notion UI の場合
```
https://www.notion.so/12345678901234567890123456789012?v=view...
                       ↑ DATABASE_ID をコピー
```

**パターン B:** 古い Notion UI または共有リンクの場合
```
https://notion.so/workspace/DB-Name-12345678901234567890123456
                          ↑ URL の末尾 32 文字
```

### Step 2: 各データベース用に DATABASE_ID を記録

| DB | Current .env (data_source_id) | New DATABASE_ID | Source |
|----|------|-------|--------|
| MEMBERS | 51c2fae4-ac36-4d51-bced-8a4b203b5768 | ? | Notion URL |
| ACTIVITIES | 4655e4e3-89f0-4852-b999-2801483bd8b5 | ? | Notion URL |
| MATCHING_HISTORY | e489e92d-fffc-4ae1-b2d1-0784a57adbfd | ? | Notion URL |
| MATCHING_RESULTS | 2e6baab3-4b6c-465d-af11-95e049e2ae9a | ? | Notion URL |
| UNMATCHED_MEMBERS | 49e6f31e-5bd6-41aa-8cc6-b2d24a61502f | ? | Notion URL |

### Step 3: .env に DATABASE_ID を追加

**.env を編集** (既存の ID は保持):

```env
# 既存の data_source_id (クエリ用)
MEMBERS_DATA_SOURCE_ID=51c2fae4-ac36-4d51-bced-8a4b203b5768
ACTIVITIES_DATA_SOURCE_ID=4655e4e3-89f0-4852-b999-2801483bd8b5
MATCHING_HISTORY_DATA_SOURCE_ID=e489e92d-fffc-4ae1-b2d1-0784a57adbfd
MATCHING_RESULTS_DATA_SOURCE_ID=2e6baab3-4b6c-465d-af11-95e049e2ae9a
UNMATCHED_MEMBERS_DATA_SOURCE_ID=49e6f31e-5bd6-41aa-8cc6-b2d24a61502f

# 新しい database_id (作成用)
MEMBERS_DB_ID=<Notion URLから抽出した32文字のID>
ACTIVITIES_DB_ID=<Notion URLから抽出した32文字のID>
MATCHING_HISTORY_DB_ID=<Notion URLから抽出した32文字のID>
MATCHING_RESULTS_DB_ID=<Notion URLから抽出した32文字のID>
UNMATCHED_MEMBERS_DB_ID=<Notion URLから抽出した32文字のID>
```

### Step 4: notion_client.py を更新

読み取り操作では DATA_SOURCE_ID を、作成操作では DB_ID を使用する:

**例:**
```python
# クエリ用 (data_source_id)
url = f"https://api.notion.com/v1/data_sources/{MEMBERS_DATA_SOURCE_ID}/query"

# 作成用 (database_id)
payload = {
    "parent": {"database_id": MEMBERS_DB_ID},
    ...
}
```

---

## 代替案: API バージョン確認

もし Notion 2026-03-11 API が data_sources での直接作成をサポートしている場合は、別のエンドポイントがあるはず:

- `POST /data_sources/{id}/rows` (試験的)
- `POST /data_sources/{id}/insert` (試験的)
- または Notion API ドキュメント参照

---

## 参考: Notion URL から ID を抽出するツール

```bash
# もし Notion の共有リンクを持っていれば
# https://www.notion.so/12345678901234567890123456789012?v=...
# の 12345678901234567890123456789012 をコピー

# または、Notion DB を開いて、
# ブラウザの Developer Tools で:
# > document.location.href
# をコピペして確認
```

