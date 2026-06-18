# Activities データベース作成ガイド

## 問題
フォームで送信した活動データが Notion に保存されていません。
理由：**ACTIVITIES_DB_ID** 環境変数が設定されていない

## 解決方法 - 2 つのオプション

### オプション A：完全自動（推奨）

```bash
cd C:\Users\yo_yo\Documents\blendy_matching
python create_activities_manual.py
```

このスクリプトは対話的に親ページ ID を入力させ、自動で Activities データベースを作成します。

---

### オプション B：手動セットアップ

Notion で 1-2 分で完了します。

#### ステップ 1：メンバーリストの親ページを確認

1. ブラウザで Notion を開く
2. メンバーリストデータベース（👥 メンバーリスト）をクリック
3. 親ページを確認：
   - 左サイドバーでメンバーリストを右クリック
   - または、URL を確認：
     ```
     https://www.notion.so/[親ページID]/[メンバーリストDB]
     ```

#### ステップ 2：新しいデータベースを作成

メンバーリストの **同じ親ページ内**で以下の手順を実行：

1. Notion ページ内で `+` をクリック → `Database` を選択
2. データベース名：**Activities**
3. タイプ：**Database** を選択

#### ステップ 3：プロパティを追加

以下のプロパティを追加してください：

```
Title Property:
  - アクティビティ名 (Title/タイトル)

Other Properties:
  - サービス内容 (Text)
  - 対象業界 (Text)
  - 対象企業規模 (Select)
    Options: スタートアップ | 中小企業 | 中堅企業 | 大企業
  
  - 強み (Multi-select)
    Options:
      技術・開発力
      営業・営業ネットワーク
      業界知見・実績
      ブランド・認知度
      コンテンツ・教材
      その他
  
  - 強み_詳細 (Text)
  
  - 課題 (Multi-select)
    Options:
      営業・マーケティング力
      技術・開発力
      営業ネットワーク・顧客基盤
      資金・人材・リソース
      業界知見・実績
      その他
  
  - 課題_詳細 (Text)
  
  - ポジション (Multi-select)
    Options:
      認知・ブランディング
      集客・マーケティング
      リード獲得・見込み客育成
      営業・提案・クロージング
      制作・開発・導入
      運用・保守・継続支援
      教育・研修・人材育成
      経営・戦略・資金調達
  
  - Member (Relation → メンバーリストDB を選択)
```

#### ステップ 4：データベース ID を取得

1. Activities データベースを開く
2. URL をコピー：
   ```
   https://www.notion.so/[DATABASE_ID]?v=...
   ```
3. `DATABASE_ID` 部分をコピー（ハイフン付き：`a1b2c3d4-e5f6-7890-abcd-ef1234567890`）

#### ステップ 5：.env を更新

`C:\Users\yo_yo\Documents\blendy_matching\.env` を編集：

```bash
# 既存の行の後に追加
ACTIVITIES_DB_ID="[コピーしたID]"
```

例：
```bash
MEMBERS_DB_ID=517b9ae4-8e9d-496d-b581-927bde2af2fe
ACTIVITIES_DB_ID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### ステップ 6：サーバー再起動

```bash
# サーバーを停止（Ctrl+C）
# その後、サーバーを起動
python main.py
```

#### ステップ 7：テスト

1. http://localhost:8000/register-multiactivity にアクセス
2. フォームを入力・送信
3. Notion で Activities データベースに新レコードが追加されることを確認

---

## トラブルシューティング

### エラー：`AttributeError: 'NoneType' object has no attribute` 

→ ACTIVITIES_DB_ID が `.env` に設定されていません  
解決：オプション A または B を実行してください

### エラー：`400 Bad Request: Invalid database ID format`

→ データベース ID のフォーマットが正しくありません  
確認：ID にハイフンが含まれているか  
正しい形式：`a1b2c3d4-e5f6-7890-abcd-ef1234567890`

### Notion に記録が追加されない

→ Notion インテグレーション権限の確認  
解決：
1. Notion ワークスペース設定 → インテグレーション
2. 「ブレンディーマッチング」を選択
3. Activities データベースへのアクセス権を付与

---

## 関連ファイル

- `notion_client.py` - `create_activity()` 実装
- `main.py` - `/api/register-multiactivity` エンドポイント
- `.env` - 環境変数設定ファイル
