# 申込フォーム共有ガイド

外部ユーザーに申込フォームを共有する簡単な方法です。

---

## 📋 前提条件

1. **Python** がインストール済み
   - `python --version` で確認
   - インストール: https://www.python.org/

2. **ngrok** (外部公開の場合のみ)
   - `ngrok --version` で確認
   - インストール: https://ngrok.com/download
   - 登録: https://dashboard.ngrok.com/signup

---

## 🚀 クイックスタート

### Windows ユーザー

1. **フォルダを開く**
   ```
   C:\Users\yo_yo\Documents\blendy_matching
   ```

2. **`deploy.bat` をダブルクリック**
   - 自動でサーバーとngrokが起動します
   - 画面に表示される URL をコピーして外部ユーザーに送信

### Mac / Linux ユーザー

1. **ターミナルで実行**
   ```bash
   cd ~/Documents/blendy_matching
   python deploy.py
   ```

2. 画面に表示される URL をコピーして外部ユーザーに送信

---

## 📊 共有 URL の確認方法

### 方法1: ngrokコンソール（推奨）

1. ブラウザで `http://localhost:4040` を開く
2. **Forwarding** に表示される URL をコピー
   ```
   https://abc123xyz.ngrok.io
   ```

3. 以下の URL を外部ユーザーに送信:
   ```
   フォーム: https://abc123xyz.ngrok.io/register
   ダッシュボード: https://abc123xyz.ngrok.io/
   ```

### 方法2: ngrok ターミナル

ngrok起動時のターミナルに以下のように表示:
```
Forwarding     https://abc123xyz.ngrok.io -> http://localhost:8001
```

`https://abc123xyz.ngrok.io` をコピーして使用

---

## 🔗 URL 一覧

| 用途 | URL |
|------|-----|
| 📝 申込フォーム | `https://xxx.ngrok.io/register` |
| 📊 ダッシュボード | `https://xxx.ngrok.io/` |
| 🔍 マッチング結果 | `https://xxx.ngrok.io/` (ダッシュボード内) |

---

## ❓ よくある質問

### Q: ngrokをインストールしたい

```bash
# Windows
# https://ngrok.com/download から exe をダウンロード

# Mac
brew install ngrok

# Linux
curl https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
unzip ngrok-v3-stable-linux-amd64.zip
sudo mv ngrok /usr/local/bin
```

### Q: ngrokを認証したい

1. https://dashboard.ngrok.com/signup で登録
2. ダッシュボードから Auth Token を取得
3. 以下を実行:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Q: ポート 8001 が既に使用中の場合

**デプロイスクリプトが自動で処理します**

手動で解放したい場合:
```bash
# Windows
netstat -aon | find ":8001"
taskkill /F /PID <PID>

# Mac/Linux
lsof -ti:8001 | xargs kill -9
```

### Q: ローカルのみでテストしたい

`deploy.py` の最後で ngrok 無しで実行している場合:
```
http://localhost:8001/register
http://localhost:8001/
```

でアクセス可能です（外部からはアクセス不可）

### Q: 24時間後に接続が切れた

再度 `deploy.bat` または `deploy.py` を実行して下さい

新しい URL が発行されます

### Q: エラーが出た場合

#### サーバーが起動しない
```
❌ エラーが発生しました: ...
```
→ 依存パッケージをインストール:
```bash
pip install -r requirements.txt
```

#### ngrok がインストール検出されない
```
❌ ngrokがインストールされていません
```
→ https://ngrok.com/download から手動でインストール

#### ファイアウォールエラー
```
❌ Windowsファイアウォールが...
```
→ 以下を管理者権限で実行:
```bash
netsh advfirewall firewall add rule name="Blendy" dir=in action=allow protocol=tcp localport=8001
```

---

## 🔒 セキュリティについて

- **ngrok URL は誰でもアクセス可能です**
  - 信頼できるユーザーのみに共有してください
  - 24時間で自動的に切れます

- **データ保護**
  - 送信データは Notion に自動保存されます
  - バックアップは定期的に実施してください

---

## 📱 動作確認

1. フォームにアクセス
   ```
   https://xxx.ngrok.io/register
   ```

2. テストデータを入力して送信

3. ダッシュボードで確認
   ```
   https://xxx.ngrok.io/
   ```

4. Notion データベースで確認
   - https://www.notion.so/xxx (プロジェクト内で設定)

---

## 🆘 トラブルシューティング

| 問題 | 解決策 |
|------|--------|
| フォームが 404 | サーバーが起動しているか確認 (localhost:8001) |
| 送信後エラー | Notion API キーが正しいか確認 |
| データが保存されない | Notion データベース接続を確認 |
| ngrok が起動しない | アカウント認証を確認: `ngrok config list` |

---

## 📞 サポート

問題が解決しない場合:
- Notion API キー設定を確認
- ターミナルのエラーメッセージを確認
- `main.py` の `notion_client` インポートを確認

---

**最終確認チェックリスト:**
- [ ] サーバーが localhost:8001 で起動中
- [ ] ngrok が起動中 (localhost:4040 で確認可)
- [ ] フォーム URL を外部ユーザーに共有
- [ ] テスト送信で動作確認完了
