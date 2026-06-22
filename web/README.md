# Blendy Web (v2)

協業マッチング v2 のフロントエンド/サーバ。**Next.js (App Router) + Supabase + Claude**。

設計: [`../docs/superpowers/specs/2026-06-22-rebuild-v2-design.md`](../docs/superpowers/specs/2026-06-22-rebuild-v2-design.md)
トラッキング: GitHub Issue #16

## セットアップ

```bash
cd web
cp .env.example .env.local   # 値を埋める（無くてもモードで動く）
npm install
npm run dev                  # http://localhost:3000
```

### 環境変数
| 変数 | 用途 |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 接続（認証/DB） |
| `SUPABASE_SERVICE_ROLE_KEY` | サーバ側の管理操作（取り扱い注意） |
| `ANTHROPIC_API_KEY` | Claude（プロフィール生成 / 議事録更新）。サーバ側のみ |

> **キーが無くても動きます**: Supabase 未接続時はモックデータでスワイプ画面が、`ANTHROPIC_API_KEY` 未設定時は AI 機能がモック応答で動作確認できます（叩き）。

## 構成
```
web/
├── src/
│   ├── app/                 App Router（画面 + API Route）
│   │   ├── page.tsx         ランディング
│   │   ├── signup / login   認証（E2）
│   │   ├── profile/         会社プロフィール編集 + generate（E3）
│   │   ├── discover/        スワイプ（E4）
│   │   ├── matches/         マッチ一覧（E4）
│   │   ├── meetings/        議事録→更新提案（E5）
│   │   └── api/             Claude を叩くサーバ Route
│   ├── components/          UI / SwipeDeck / SwipeCard
│   ├── theme/colors.ts      ★ カラートークン（切り出し）
│   ├── lib/                 supabase / claude / scoring(TS) / prompts
│   └── data/                モックデータ
└── supabase/migrations/     スキーマ（0001_init / 0002_rls）
```

## 色（テーマ）の変え方
`src/theme/colors.ts` と `src/app/globals.css` の CSS 変数（`:root`）の値を差し替えるだけ。
セマンティック名（`--bg` / `--surface` / `--accent` …）で参照しているため、UI 側の修正は不要。

## デプロイ
Vercel（フロント+サーバ）＋ Supabase（DB/Auth/Storage）。詳細は設計 §7 / Issue #15。

## 実装状況（叩き）
- E0 デザインシステム / ダークテーマ … ✅ トークン + 基本UI
- E1 基盤 … ⏳ スキーマ(SQL) 済 / Supabase 実接続は要キー
- E2 登録 … ✅ フォームUI（保存は要 Supabase）
- E3 AIプロフィール生成 … ✅ UI+API（要 ANTHROPIC_API_KEY、PDFパースは今後）
- E4 スワイプ … ✅ モックで動作（DB連携は要キー）
- E5 議事録更新 … ✅ 提案→承認UI + プロンプト（要キー）
- E6 公開 … ⏳ Vercel/Supabase 用意後
