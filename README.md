# 🤝 協業マッチングシステム - Blendy Inc.

ブラウザで操作できる AIマッチングシステム。メンバー申込 → AI自動マッチング → Notionで管理

---

## 📚 ファイル構成

```
blendy_matching/
├── 📝 README.md                    ← このファイル
├── 🚀 quick_share.cmd              ← クイック共有（推奨）
├── 🚀 deploy.bat                   ← デプロイバッチ（Windows）
├── 🚀 deploy.py                    ← デプロイスクリプト（汎用）
├── 📋 DEPLOY_GUIDE.md              ← 共有ガイド（詳細）
├── ✅ SHARING_CHECKLIST.md         ← 共有前チェックリスト（重要）
├── main.py                         ← FastAPI サーバーメイン
├── requirements.txt                ← 依存パッケージ一覧
├── templates/
│   ├── index.html                  ← ダッシュボード画面
│   └── register.html               ← 申込フォーム画面
├── notion_client.py                ← Notion API 連携
├── matching_engine.py              ← AIマッチングロジック
└── server.log                       ← サーバーログ
```

---

## 🎯 使い方（3ステップ）

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
