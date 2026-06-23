# プロジェクト状況メモ（引き継ぎ / 作業ログ）

最終更新: 2026-06-23

このファイルは「今どこまで進んでいて、次に何をやるか」を一枚で把握するためのメモです。
リポジトリ移行後もここを起点に再開できます。

---

## 1. 何を作っているか
**Blendy 協業マッチング v2**（既存 FastAPI+Notion を作り替え中）。
- スタック: **Next.js(App Router) + Supabase(Postgres/Auth/Storage) + Claude + Voyage(埋め込み)**
- ホスティング: **Vercel**（フロント+サーバ）、DB は Supabase
- アプリ本体は **`web/`** ディレクトリ（モノレポ風）。旧 Python 一式はルートに残置（将来 `legacy/` へ）

### 確定した方針（ブレストで合意済み）
- マッチング = **相互Like型（Tinder風だがB2Bトーン）**。AIスコアはランキングに使用
- アカウント = **1アカウント=1企業**
- 議事録更新 = **提案→承認型**（差分レビュー）
- デザイン = ダーク基調・**カラートークン切り出し**（`web/src/theme/colors.ts` + `globals.css`）
- 埋め込み = **Voyage AI(voyage-3/1024次元) → Supabase pgvector**
- カレンダー = **アプリ内（MVP）**

---

## 2. 設計ドキュメント（必読）
- `docs/superpowers/specs/2026-06-22-rebuild-v2-design.md` … v2 全体設計（E0〜E6）
- `docs/superpowers/specs/2026-06-23-history-calendar-vector-design.md` … 履歴/カレンダー/ベクトル（E7〜E9）
- `docs/architecture/target-architecture.md` … 旧→Postgres移行の考え方
- `docs/guides/Anthropic_APIキー取得手順.pdf` … クライアント送付用（Claudeキー取得手順）
- `docs/ONBOARDING.md` … 必要な権限・各種アカウントの準備手順

---

## 3. 実装状況（web/）
| Epic | 内容 | 状態 |
|---|---|---|
| E0 デザインシステム | カラートークン切り出し・ダーク・基本UI・**B2Bトーン+レスポンシブ(PC/スマホ)** | ✅ 実装済 |
| E1 基盤 | Next.js scaffold / Supabaseクライアント / スキーマSQL(0001,0002) | ✅ コード済・**実接続は要キー** |
| E2 登録 | signup/login フォーム（最低限項目） | ✅ UI済・**users/companies保存は未結線** |
| E3 AIプロフィール生成 | `/profile/generate` + API（Claude、未設定時モック） | ✅ UI/API済・**PDFパース未** |
| E4 スワイプ | SwipeDeck/Card・親和性スコアTS移植・matches一覧 | ✅ **モック動作**・実DB未 |
| E5 議事録 | `/meetings` + API（提案→承認・こだわりプロンプト） | ✅ UI/API済・実DB未 |
| E6 公開 | Vercel+Supabase 本番化 | ⏳ 設定中 |
| E7 履歴 | match_outcomes・/history | 🔵 **設計のみ**（未実装） |
| E8 カレンダー | calendar_events・/calendar | 🔵 **設計のみ**（未実装） |
| E9 ベクトル基盤 | 資料全保管・Voyage埋め込み・pgvector・合う/合わない分析 | 🔵 **設計のみ**（未実装） |

ビルド確認済み: `cd web && npm install && npm run build` → 全ルート成功。
キー無しでもモックで全画面が動く（`npm run dev` → http://localhost:3000）。

---

## 4. GitHub Issue
- 親 **#16**（v2リビルド トラッキング）
- #9 E0 / #10 E1 / #11 E2 / #12 E3 / #13 E4 / #14 E5 / #15 E6
- （E7/E8/E9 は設計済。Issue化は移行後に再作成推奨）

> ⚠️ リポジトリを別アカウントへ `--mirror` で複製すると、**Issue/PRは複製されません**（git refのみ）。
> 移行後は新リポで Issue を作り直してください（本ファイルと各設計docがあれば再現可能）。

---

## 5. インフラ設定の進捗（2026-06-23時点）
- **Supabase**: ユーザーが作成中。プロジェクト `nhbsxqmdypcnnypukwnq`。
  - `NEXT_PUBLIC_SUPABASE_URL` = `https://nhbsxqmdypcnnypukwnq.supabase.co`（`/rest/v1/` は付けない）
  - publishable key → `NEXT_PUBLIC_SUPABASE_ANON_KEY` / secret key → `SUPABASE_SERVICE_ROLE_KEY`
  - やること: SQL Editor で `web/supabase/migrations/0001_init.sql`→`0002_rls.sql` を実行 / Database>Extensions で `vector` 有効化 / Storage に `materials`(Private) バケット作成
- **Vercel**: ユーザーが作成中。**Root Directory = `web` 必須**。環境変数に上記3つ＋`ANTHROPIC_API_KEY`＋`NEXT_PUBLIC_USE_MOCK=false`。
- **仕上げ**: Supabase Authentication > URL Configuration に Vercel本番URL（＋localhost:3000）を登録
- **Claude キー**: クライアントが用意（PDF手順を送付）。受領後 Vercel に `ANTHROPIC_API_KEY` 登録
- **Voyage キー**: E9実装時に `VOYAGE_API_KEY` を追加

---

## 6. 次にやること（おすすめ順）
1. **E1 実接続**（#10）: signup → `companies`/`users` 保存（Server Action + RLS）、ログイン後セッション
2. **E3 実装の肉付け**（#12）: HP本文取得・PDFパース → Voyage埋め込みの土台
3. **E4 実DB化**（#13）: swipes/matches を Supabase に、相互Like→マッチ成立
4. **E5 実DB化**（#14）: meetings/proposals 保存、承認で profiles/sales_notes 反映
5. **E7/E8/E9 実装**: migrations 0003(履歴/カレンダー)/0004(pgvector) 追加 → UI（/history,/calendar,/insights）→ Voyage連携
6. **E6 公開**（#15）: 独自ドメイン・利用規約・本番確認

---

## 7. ローカルでの動かし方
```bash
cd web
cp .env.example .env.local   # キーがあれば記入。無くてもモックで動く
npm install
npm run dev                  # http://localhost:3000
```
色変更は `web/src/theme/colors.ts` と `web/src/app/globals.css` の `:root` の値だけ。
