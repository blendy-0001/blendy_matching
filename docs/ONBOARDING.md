# 開発引き継ぎ・必要アクセス権限チェックリスト

この先の開発・運用を進めるうえで、リポジトリのオーナー（発注元 / 友人）から
受け取っておきたいアカウント・APIキー・権限の一覧です。
**秘密情報はコード／リポジトリに含めず**、`.env`（ローカル）または Render ダッシュボード
（本番 Secrets）で管理してください。

> 凡例: 🔴 必須（これが無いと動かない） / 🟡 本番運用に必要 / 🟢 任意・あると便利

---

## 1. Notion（実データストア）🔴
本システムは Notion を実DBとして利用しているため、最重要。

- [ ] 🔴 **Notion Integration Token**（`NOTION_API_KEY`）
  - https://www.notion.so/my-integrations で発行された Integration のトークン
- [ ] 🔴 **各 Notion データベースの ID**（`*_DB_ID`）
  - メンバー / マッチング履歴 / マッチング結果 / 未マッチ / アクティビティ 等
  - 既存値は `config.py` の `os.getenv(...)` キー名を参照
- [ ] 🔴 **Integration を各 DB に「接続（共有）」してもらう**
  - トークンがあっても、対象 DB に Integration が共有されていないと API でアクセス不可
- [ ] 🟢 ワークスペース自体の閲覧権限（DB スキーマ確認・デバッグ用）

## 2. Anthropic Claude（AI 補助）🟡
マッチングのシナジー加点に使用（無くてもルールベースで動作）。

- [ ] 🟡 **Claude API キー**（`CLAUDE_API_KEY`）
  - https://console.anthropic.com で発行
  - ※ 現状 `render.yaml` 未定義のため、本番では別途ダッシュボード設定が必要

## 3. Render.com（ホスティング）🟡
本番デプロイ・環境変数・ログ確認のため。

- [ ] 🟡 **Render アカウントへのチームメンバー招待**（または共有アカウント）
  - 対象サービス: `blendy-matching`（`render.yaml` 参照）
- [ ] 🟡 環境変数 / Secrets の閲覧・編集権限（`NOTION_API_KEY`, `*_DB_ID`, `API_KEY`, `CLAUDE_API_KEY` 等の設定）
- [ ] 🟡 デプロイ実行・ログ閲覧権限（障害調査・再デプロイ用）
- [ ] 🟢 課金プラン変更権限（free→有料：永続ディスク / スリープ回避が必要になった場合）

## 4. GitHub（ソースコード）🔴
- [ ] 🔴 **リポジトリへの Collaborator 権限**（`blendy-0001/blendy_matching`、push / PR 作成）
- [ ] 🟢 ブランチ保護・マージ設定の確認（運用ルール合わせ）
- [ ] 🟢 GitHub Actions 等 CI を今後入れる場合の Secrets 設定権限

## 5. アプリ内認証キー 🟡
- [ ] 🟡 **`API_KEY`** の現行値（ダッシュボード / マッチング実行の認証）
  - 本番で稼働中の値を共有してもらうか、ローテーション方針を決める
  - ※ 現状 `render.yaml` 未定義のため、本番では別途ダッシュボード設定が必要

## 6. その他・任意 🟢
- [ ] 🟢 **ngrok の Authtoken**（ローカルから外部共有する場合。README のフロー参照）
- [ ] 🟢 独自ドメインを使う場合の DNS 管理権限
- [ ] 🟢 営業資料（`docs/sales/`）の編集元データ・ブランド素材

---

## 受け取り後にやること
1. ローカル: `cp .env.example .env` して各値を記入（`.env` は `.gitignore` 済み）
2. 本番: Render ダッシュボードで Secrets / 環境変数を設定
3. 動作確認: `uvicorn blendy.main:app --app-dir src --reload` → `/docs` で疎通確認
4. `pytest` でテストが通ることを確認

> 🔒 受領した秘密情報は安全な経路（パスワードマネージャ / 暗号化チャネル）で受け渡しし、
> Slack やメール平文での共有は避けてください。

---

# 付録: 権限付与の詳細手順（付与する側＝オーナー向け）

## A. GitHub の権限付与（個人リポジトリのコラボレーター招待）

> 本リポジトリのオーナー `blendy-0001` は **個人(User)アカウント**のため、以下は
> 個人リポジトリのコラボレーター招待フロー。招待相手の GitHub ユーザー名を事前に確認しておく。

1. リポジトリを開く → 上部タブ **Settings**（Admin のみ表示）
2. 左サイドバー **Collaborators**（「Access」セクション内）
3. 2FA 設定時はパスワード / 認証の再確認 → 認証
4. **「Add people」** → 相手の **GitHub ユーザー名 or メールアドレス** を入力して選択
5. **「Add ___ to this repository」** をクリック → 招待メール送信
6. **招待された側**が承認: 受信メールのリンク、または
   `https://github.com/blendy-0001/blendy_matching/invitations` を開いて **Accept**

> ⚠️ 個人アカウントのリポジトリでは、コラボレーターは一律 **「Write（push 可能）」**。
> Read / Triage / Write / Maintain / Admin の細かいロール分けは **Organization リポジトリのみ**。
> 複数人で権限を分けたい場合は Organization への移管を検討。

## B. Notion の権限付与（Integration 作成 → 各DBへ接続）

> Notion は「API トークンを渡すだけ」では動かない。**Integration を各 DB に『接続』する手順が必須**
> （最もハマりやすいポイント）。

### B-1. Integration を作成してトークンを取得
1. ワークスペースのオーナー / 管理者で https://www.notion.so/my-integrations を開く
2. **「New integration」** → タイプ **Internal**、対象ワークスペースを選択、名前（例: `blendy-matching`）を入力して作成
3. **Capabilities（権限）**: **Read content / Update content / Insert content** にチェック（ユーザー情報・コメントは不要）
4. **「Internal Integration Secret」** をコピー → これが `NOTION_API_KEY`（`ntn_...` または `secret_...`）

### B-2. 各データベースに Integration を「接続」 ← 最重要
アプリが使う**すべての DB** に対して繰り返す（メンバー / マッチング履歴 / マッチング結果 / 未マッチ / アクティビティ 等）。

1. 対象 DB を**フルページ**で開く
2. 右上 **「•••」** メニュー → **「Connections（接続）」** → **「+ Add connections」**
3. 作成した Integration 名を検索して選択 → **Confirm**
4. **全 DB 分**繰り返す（1 つでも漏れると、その DB だけ API でアクセスできずエラーになる）

### B-3. データベースID（`*_DB_ID`）を取得
1. DB をフルページで開き、URL をコピー
2. `https://www.notion.so/{ワークスペース}/{32桁の英数字}?v=...` の **32桁部分**が DB ID（`8-4-4-4-12` 形式のハイフン付きでも可）
3. 必要なキー名は [`config.py`](../src/blendy/config.py) を参照（`MEMBERS_DB_ID`, `MATCHING_HISTORY_DB_ID`, `MATCHING_RESULTS_DB_ID`, `UNMATCHED_MEMBERS_DB_ID`, `ACTIVITIES_DB_ID` など）

### B-4. データソースID（`*_DATA_SOURCE_ID`）を取得
本アプリは新しい Notion API の「データソース」概念も参照する（`config.py` に `*_DATA_SOURCE_ID` あり）。
URL からは取得できず、**API 経由**で取得する:
- `GET https://api.notion.com/v1/databases/{DB_ID}` のレスポンス `data_sources[].id`
- トークン設定後、リポジトリ内の `scripts/check_*.py` / `scripts/search_accessible_databases.py` 等でも確認可能
