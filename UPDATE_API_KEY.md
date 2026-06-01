# 新しい Claude API キーを設定する手順

## 📍 手順 (3ステップ、2分で完了)

### Step 1️⃣ : 新 API キーをコピー
Anthropic のダッシュボードで新しい API キーを作成し、コピーしておいてください。

```
sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

### Step 2️⃣ : .env ファイルを編集
`C:\Users\yo_yo\Documents\blendy_matching\.env` を開いて、この行を更新:

**現在:**
```
CLAUDE_API_KEY=sk-ant-api03-...【古いキー】...
```

**変更後:**
```
CLAUDE_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

> 💡 **メモ**: エディタで Ctrl+H（置換）を使うと楽です
>
> - 検索: `CLAUDE_API_KEY=sk-ant-api03-.*`
> - 置換: `CLAUDE_API_KEY=【新しいキー】`

### Step 3️⃣ : 動作確認
```bash
cd C:\Users\yo_yo\Documents\blendy_matching
python test_matching.py
```

期待される出力:
```
[RESULTS] マッチング結果:

--- マッチング 1 ---
  メンバーA: 名前A
  メンバーB: 名前B
  スコア: XX
  協業タイプ: ○○型
  マッチング理由: ...
  紹介文: 【AI が生成した完全な紹介文が表示される】
```

✅ 紹介文が **AI生成テキスト** なら成功！  
❌ 紹介文が **テンプレート** なら API キーの問題

## 🚀 本番反映

自動デプロイが有効なため、以下の流れで本番反映:

```bash
# ローカルで動作確認後
git add .env
git commit -m "Update Claude API key"
git push origin main
```

→ 自動で https://blendy-matching.onrender.com/ に反映

## ⚙️ オプション: ローカルで先にテスト

新キーを試す前に、安全にテストしたい場合:

```bash
# 1. 現在の .env をバックアップ
cp .env .env.backup

# 2. 新キーで .env を更新

# 3. テスト実行
python test_matching.py

# 4. 成功したら本番環境へ、失敗したら復元
# cp .env.backup .env
```

## 🔄 トラブル時のリセット

もし設定を間違えた場合:

```bash
# .env をリセット（デフォルト状態に）
git checkout .env

# または.env.backup から復元
cp .env.backup .env
```

---

**質問がある場合は遠慮なく聞いてください！** 🙋
