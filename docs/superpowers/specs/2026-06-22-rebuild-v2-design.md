# 設計: Blendy 協業マッチング v2 リビルド

**v1.0 | 2026-06-22 | エンジニア向け**

既存（FastAPI + Notion + サーバ生成HTML）を作り替え、**Next.js(Vercel) + Supabase** を土台に、
恋愛アプリ風スワイプUI・AI企業プロフィール生成・議事録による情報更新を備えたプロダクトへ刷新する。

関連: [方向性ドキュメント](../../ブレンディ　協業マッチング　方向性.md)

---

## 1. 決定事項（ブレインストーミングで合意）

| 論点 | 決定 |
|---|---|
| 技術スタック | **Next.js(App Router) on Vercel + Supabase(Postgres/Auth/Storage)**。AIは Claude。第2バックエンドは作らない（Nextサーバ機能で実行） |
| 既存資産 | FastAPI/Notion/HTML は `legacy/` へ退避。親和性スコアのロジックは TS へ移植 |
| マッチング | **相互Like型（Tinder風）**。AIスコアは候補のランキングに使用 |
| アカウント | **1アカウント=1企業**（登録者が企業代表） |
| 議事録更新 | **提案→承認型**（AIが差分提案、ユーザーが承認/修正して適用） |
| デザイン | ダーク/ブラック基調・シンプル洗練。**カラートークンをファイル切り出し**（後で差し替え可能） |
| AIプロフィール | 最低限登録＋HP(URL)・紹介資料(PDF)を読み込み**叩きを生成→ユーザー編集** |

---

## 2. アーキテクチャ

```
[ ユーザー(企業担当) ] ─HTTPS→ [ Vercel: Next.js(App Router/React) ]
        スワイプUI・ダーク                  │ Server Actions / Route Handlers（AIキーはサーバ側のみ）
                                            ├─→ [ Supabase ]  Postgres + Auth + Storage(PDF)
                                            └─→ [ Claude ]    プロフィール生成 / 議事録更新 / ランキング補助
```

- AI 呼び出しは**サーバ側のみ**（APIキーをクライアントに出さない）
- ファイル(PDF)は Supabase Storage、メタは Postgres
- 認証は Supabase Auth（email + password）。RLS で企業ごとにデータ分離

### リポジトリ構成（モノレポ風・同一リポ）
```
blendy_matching/
├── web/                      ← Next.js アプリ（新規・本体）
│   ├── app/                  App Router（ルート/画面）
│   ├── components/           UI コンポーネント
│   ├── lib/                  supabase client, claude client, scoring(TS移植)
│   ├── theme/                ★ colors.ts / tokens（カラー切り出し）
│   └── supabase/             migrations(SQL) / seed
├── legacy/                   ← 旧 FastAPI/Notion 一式を退避
└── docs/                     既存ドキュメント群
```

---

## 3. データモデル（Supabase Postgres）

| テーブル | 主カラム | 備考 |
|---|---|---|
| `companies` | id, name(会社名), industry(業種), officer_count(役員数), employee_count(従業員数), revenue_scale(売上規模, null可), website_url(HP), created_at | |
| `users` | id(=auth.uid), company_id(1:1, unique), full_name(氏名), role_title(役職), email | Supabase Auth と紐付け |
| `company_profiles` | company_id(PK), summary(AI生成), value_prop, strengths, challenges, target_market, is_edited(bool), updated_at | 編集可能な叩き |
| `profile_sources` | id, company_id, type(website/pdf), url, storage_path, extracted_text, created_at | プロフィール生成の入力 |
| `company_attributes` | company_id(PK), 施策活動(text[]), 意思決定スタイル, 時間軸, コミットレベル, 協調スタイル, 協業経験 | ランキング用（L2/L3移植） |
| `swipes` | id, swiper_company_id, target_company_id, direction(like/pass), created_at, **unique(swiper,target)** | |
| `matches` | id, company_a_id, company_b_id(a<b 正規化), created_at, **unique(a,b)** | 相互Likeで生成 |
| `meetings` | id, match_id, minutes_text, uploaded_by_company_id, created_at | 商談議事録 |
| `profile_update_proposals` | id, meeting_id, company_id, changes(jsonb 差分), status(pending/approved/rejected), created_at, applied_at | 提案→承認 |
| `sales_notes` | company_id, content(営業情報), updated_at | 議事録で育つ |

- RLS: `users.company_id` を軸に、自社データは編集可・他社は公開プロフィールのみ閲覧可。
- 既存の L2/L3 enum（profile_schema 相当）は TS の型として再定義。

---

## 4. 主要フロー

### 4.1 登録 → AI企業プロフィール生成
1. サインアップ（Supabase Auth）。最低限項目を入力:
   **氏名 / 役職 / 会社名 / ログイン情報(email+password) / 役員(数) / 業種 / 売上規模(任意) / 従業員数**
2. 追加情報: **HP の URL** と **会社紹介資料(PDF)** を登録
3. サーバ側で HP を取得（本文抽出）＋ PDF をパース → `profile_sources` に保存
4. Claude が叩きプロフィール（summary / 価値提供 / 強み / 課題 / 対象市場）を生成 → `company_profiles`
5. ユーザーが画面で編集・確定（`is_edited=true`）

### 4.2 スワイプマッチング（相互Like）
1. `company_attributes` ＋親和性スコア（TS移植）で候補をランキング
2. 既に swipe 済み / マッチ済みを除外しデッキ生成
3. Like/Pass を `swipes` に記録
4. 相手も自社に Like 済みなら `matches` 生成 → 通知 → 連絡/チャットへ
5. マッチ後チャットは E4 に最小実装（or 後続Issue）

### 4.3 議事録インジェスト（提案→承認）
1. マッチ後、商談議事録を投入（テキスト貼付 or アップロード）→ `meetings`
2. Claude が現 `company_profiles` / `sales_notes` と突合し、**更新差分**を生成（こだわりプロンプト・§6）
3. `profile_update_proposals` に差分(jsonb)を保存し、画面で差分レビュー
4. ユーザーが承認 → 該当フィールドへ適用（履歴は proposals に残る）、却下 → 破棄

---

## 5. デザインシステム

- `web/theme/colors.ts`（または `tokens.css` の CSS 変数）に**カラートークンを集約**
  - main=黒系。背景/サーフェス/テキスト/アクセント/ボーダーをセマンティック名で定義 → 後で値だけ差し替え可能
- 3層トークン: primitive(色値) → semantic(役割) → component(用途)
- 方針: ダーク基調・余白広め・角丸・控えめなアクセント1色。スワイプカードは大きめで写真/ロゴ映え重視

---

## 6. 議事録プロンプト設計（こだわり）

目的: 議事録から「企業プロフィール」「営業情報」を**事実ベースで**更新する差分を作る。

- **役割**: 「B2B企業情報のリサーチアナリスト。議事録から確度の高い更新のみ抽出」
- **入力**: 現プロフィール(JSON) + 現営業メモ + 議事録全文
- **指示**:
  - 議事録に明示された事実のみ反映。推測・誇張は禁止（不明は触れない）
  - フィールド単位で `{field, before, after, evidence(議事録の根拠引用), confidence}` を出力
  - 営業情報は「課題・予算・決裁者・時間軸・次アクション」を構造化
  - 既存と矛盾する場合は上書きでなく「要確認」フラグ
- **出力**: 差分提案の JSON（承認画面がそのまま描画できる形）
- 低 confidence は既定で未チェック。プロンプトは反復改善前提でバージョン管理。

---

## 7. 公開 / デプロイ

- **フロント+サーバ**: Vercel（Next.js）。プレビュー/本番の自動デプロイ
- **DB/Auth/Storage**: Supabase（`DATABASE_URL` / `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SERVICE_ROLE`）
- **AI**: `ANTHROPIC_API_KEY`（Vercel の環境変数・サーバ側のみ）
- ドメイン設定、RLS 有効化、最小限の利用規約/プライバシーを用意
- 旧 Render/Notion は段階的に停止

---

## 8. Epic 分解（→ GitHub Issue 化）

| 順 | Epic | 主な成果物 | 依存 |
|---|---|---|---|
| 1 | **E0 デザインシステム/ダークテーマ** | カラートークン切り出し・基本UI | — |
| 2 | **E1 基盤** | Next.js+Supabase+Auth+Vercel CI/CD・スキーマ(migrations) | E0 |
| 3 | **E2 登録** | サインアップ＋最低限項目（1アカウント=1企業） | E1 |
| 4 | **E3 AI企業プロフィール生成** | HP+PDF→叩き生成→編集 | E1,E2 |
| 5 | **E4 スワイプマッチング** | デッキ/Like/Pass/相互マッチ/ランキング(+最小チャット) | E1〜E3 |
| 6 | **E5 議事録インジェスト** | 提案→承認の差分更新（プロンプト重視） | E1,E3 |
| 7 | **E6 公開/本番化** | 本番デプロイ・ドメイン・環境変数・規約 | 全体 |

各 Epic は独立 Issue とし、E0→E6 の順で実装。各 Issue が個別の spec/plan を持つ。

---

## 9. 非対象（将来）
- 多人数/権限（1企業=複数ユーザー）
- 高度なチャット（既読/添付/通知の作り込み）
- 課金/成果報酬（方向性ドキュメント Phase3）
- レコメンドの機械学習化（当面はルール＋Claude）
