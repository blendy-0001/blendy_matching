# 🚀 START HERE - すぐに始める

外部ユーザーにフォームを共有するための **最短手順**

---

## ⚡ 最速スタート（3ステップ）

### Step 1️⃣ : セットアップ確認（初回のみ・1分）

```bash
python verify_setup.py
```

✅ すべてチェックで完了

### Step 2️⃣ : サーバー起動（毎回・1秒）

**Windows:** `quick_share.cmd` をダブルクリック

**その他:**
```bash
python deploy.py
```

### Step 3️⃣ : URL を共有（30秒）

```
表示される URL をコピーして外部ユーザーに送信
例: https://abc123.ngrok.io/register
```

---

## 📝 チェックリスト版

外部共有前に必ず実行：

- [ ] `python verify_setup.py` でセットアップ確認
- [ ] `quick_share.cmd` または `python deploy.py` で起動
- [ ] テスト送信: `https://xxx.ngrok.io/register`
- [ ] ダッシュボード確認: `https://xxx.ngrok.io/`
- [ ] Notion DB に記録されたか確認
- [ ] エラーがないことを確認
- [ ] ✅ → 外部ユーザーに URL を送信

詳細は `SHARING_CHECKLIST.md` を参照

---

## 🎯 よくある用途別ガイド

### シーン1: とにかく今すぐ試したい

```bash
python deploy.py
→ localhost:8001/register にアクセス
```

**所要時間:** 30秒

---

### シーン2: 外部ユーザーに送りたい

```bash
1. python verify_setup.py で確認
2. quick_share.cmd を実行
3. ngrok URL をコピー
4. https://xxx.ngrok.io/register を送信
```

**所要時間:** 1分

詳細 → `SHARING_CHECKLIST.md`

---

### シーン3: エラーが出た

**ステップ1:** ターミナルのエラーメッセージを読む

**ステップ2:** 以下から該当項目を見つける：
- "python が見つかりません" → Python をインストール
- "モジュール xxx が見つかりません" → `pip install -r requirements.txt`
- "ポート 8001 が使用中" → スクリプトが自動処理（再実行）
- "ngrok が見つかりません" → ngrok をインストール（https://ngrok.com/download）

**ステップ3:** `DEPLOY_GUIDE.md` のトラブルシューティング参照

---

## 📚 ドキュメント地図

| 目的 | ファイル |
|------|---------|
| ⚡ 最速スタート | **このファイル** |
| 🔍 セットアップ確認 | `verify_setup.py` |
| 📋 共有前チェック | `SHARING_CHECKLIST.md` |
| 📖 詳細ガイド | `DEPLOY_GUIDE.md` |
| 🎯 使い方全般 | `README.md` |

---

## 🔥 実際の流れ（例）

```
朝8時：
  1. quick_share.cmd をダブルクリック
  2. ngrok コンソール (localhost:4040) から URL をコピー
  3. Slack で全員に送信
     「メンバー申込: https://abc123.ngrok.io/register」

昼12時：
  1. ダッシュボード (https://abc123.ngrok.io/) で新規申込確認
  2. マッチング実行ボタンをクリック
  3. 結果を確認して LINE グループで紹介文を送信

夜18時：
  1. Notion データベースで全記録確認
  2. 終了: Ctrl+C で quick_share.cmd を終了
```

---

## 💡 重要ポイント

| 項目 | 説明 |
|------|------|
| 🕐 有効期限 | 24時間 |
| 👥 複数ユーザー | ✅ 同時アクセス OK |
| 🔓 セキュリティ | URL を知ってる人なら誰でもアクセス |
| 🔄 再利用 | 24時間後に新 URL 発行 |
| 💾 データ | 自動的に Notion に保存 |

---

## ❓ Q&A（よくある質問）

**Q: どのファイルを実行すればいい？**
A: Windows なら `quick_share.cmd`、それ以外なら `python deploy.py`

**Q: エラーが出た**
A: `DEPLOY_GUIDE.md` のトラブルシューティング参照

**Q: ローカルのみでテストしたい**
A: `http://localhost:8001/register` でアクセス（ngrok なしで OK）

**Q: 外部ユーザーが送信したデータはどこに保存される？**
A: Notion データベースに自動保存

**Q: 24時間後は？**
A: URL が切れます。再度デプロイして新 URL 発行

**Q: 複数回送信できる？**
A: ✅ OK。何回でも送信できます

---

## 🎬 動画見た感覚で実行

1. **Setup**
   ```bash
   python verify_setup.py
   ```

2. **Launch**
   ```bash
   # Windows
   quick_share.cmd
   
   # Other
   python deploy.py
   ```

3. **Share**
   ```
   https://xxx.ngrok.io/register
   ```

4. **Verify**
   ```
   https://xxx.ngrok.io/
   ```

5. **Send to users**
   ```
   Copy & paste URL
   ```

---

## ✨ これだけは覚えておいて

```
クイック共有:
  quick_share.cmd をダブルクリック
  → URL をコピー
  → 外部ユーザーに送信

テスト:
  http://localhost:8001/register

確認:
  http://localhost:8001/
```

---

## 🆘 もし何か分からなかったら

1. **README.md** を読む
2. **SHARING_CHECKLIST.md** でチェック
3. **DEPLOY_GUIDE.md** でトラブルシューティング

それでも分からなければ、エラーメッセージをスクリーンショットして確認

---

**準備できたら → さあ、始めましょう！** 🎉

```bash
python deploy.py
```
