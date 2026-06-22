# ターゲット構成: データ層刷新（Notion → Postgres）

**v1.0 | 2026-06-22 | 関連 Issue: #5**

現状分析（インフラ相談の結論）を踏まえ、**ホスト変更より先にデータ層を刷新する**ための
ターゲット構成と段階移行プランを定義する。

---

## 1. 現状と課題

```
[ ユーザー ] ─HTTPS→ [ Render: uvicorn + FastAPI(単一プロセス) ] ─REST→ [ Notion(実DB) ]
                          │ matching_state(インメモリ) / BackgroundTasks      └→ [ Claude(任意) ]
```

| 課題 | 内容 |
|---|---|
| **Notion を実DB代用** | 遅い・レート制限・JOIN/集計/トランザクション不可・型保証なし |
| **インメモリ状態** | `matching_state` がプロセス内 → 水平スケール不可・再起動で消失 |
| **揮発バックアップ** | `backups/` がローカル書込（free プランで消える） |

→ Vercel 等へのホスト変更では上記は解決しない。**効くのはデータ層の刷新**。

---

## 2. ターゲット構成

```
[ ユーザー ] ─HTTPS→ [ Render: FastAPI ]
                         │
                         ├─(主)→ [ Supabase Postgres ]  ← 実DB（CRUD / 集計 / 成功率追跡）
                         │           ▲
                         │           │ 任意同期（運用UI用）
                         ├─(任意)→ [ Notion ]            ← 閲覧・運用UIに降格
                         └─(補助)→ [ Claude ]
```

| レイヤ | 採用 | 理由 |
|---|---|---|
| DB | **Supabase（managed Postgres）** | バッテリー同梱（Postgres+REST+Auth）。将来 `X-API-Key` 認証も巻取り可。代替: Neon |
| アクセス層 | **Repository パターン + SQLAlchemy 2.0 + Alembic** | データソースを抽象化し Notion 依存を剥がす。マイグレーションをコード管理 |
| ドライバ | psycopg3 / asyncpg | Postgres 標準 |
| 状態管理 | `jobs` テーブル（将来 Redis 検討） | インメモリ状態を外出し → スケール対応 |
| ホスト | Render 維持 | 常駐 ASGI に適合。Vercel 化は「フロント分離後」に再検討（別Issue） |

---

## 3. データモデル（初期スキーマ）

既存 Notion DB と PR #4 の L2/L3 を実テーブル化する。

| テーブル | 主なカラム |
|---|---|
| `members` | id, 名前, 会社名, 業種カテゴリ, 業種詳細, 事業フェーズ, line_id, facebook_url, ステータス, created_at |
| `member_affinity` (or members に内包) | member_id, 施策活動(text[]), 意思決定スタイル, 時間軸, コミットレベル, 協調スタイル, 協業経験, ビジョン記述 |
| `activities` | id, member_id, 名称, サービス, 対象業界, 対象企業規模, 強み(text[]), 課題(text[]), ポジション(text[]) |
| `matching_results` | id, member_a_id, member_b_id, スコア, l1_score, 親和性スコア, スコア内訳(jsonb), 協業タイプ, 理由, run_id, created_at |
| `matching_history` | id, member_a_id, member_b_id, matched_at |
| `unmatched_members` | id, member_id, run_id, 理由 |
| `matching_outcome` | id, result_id, 状態(成功/失敗/継続検討), 追跡日, メモ |  ← 方向性ドキュメント Week7-8 |
| `jobs` | id, type, status(running/done/error), progress, request_id, last_result(jsonb), updated_at |  ← matching_state の置換 |
| `error_logs` | id, level, message, context(jsonb), created_at |

- L2/L3 の enum はアプリ側（`profile_schema.py`）を正とし、DB は text + CHECK 制約。
- `スコア内訳` は jsonb で `AffinityBreakdown` をそのまま格納。

---

## 4. 段階移行プラン（Strangler パターン）

各フェーズは独立した PR とし、いつでも切り戻せるようにする。

### Phase 0: データアクセス層の抽象化（コードのみ・挙動不変）
- `repositories/` を新設し、`MemberRepository` 等のインターフェースを定義
- 既存の `notion_client` 呼び出しを **Notion 実装(`NotionMemberRepository`)** の裏に隠す
- アプリ（main / matching_engine）は Repository 越しにのみアクセス
- **この時点では DB は変わらない**（リスクゼロのリファクタ）

### Phase 1: Postgres 基盤
- Supabase プロジェクト作成、`DATABASE_URL` を Secret 化
- SQLAlchemy モデル + Alembic 初期マイグレーションでスキーマ作成
- `PostgresMemberRepository` 等を実装（read/write）

### Phase 2: デュアルライト + 検証
- 書込を **Notion と Postgres の両方**へ（フラグ制御）
- 既存 Notion データを一括インポートするスクリプト（`scripts/migrate_notion_to_pg.py`）
- 整合性検証（件数・主要フィールド突合）

### Phase 3: カットオーバー
- 読込を Postgres に切替（`DATA_BACKEND=postgres`）
- Notion は任意の同期（運用UI）に降格 or 廃止
- `matching_state` → `jobs` テーブルへ移行

### Phase 4: クリーンアップ
- 不要になった Notion 専用コード/Secret を整理
- 集計・成功率ダッシュボード（方向性ドキュメント Week5-8）を Postgres ベースで実装

---

## 5. 移行に必要なもの（オーナー手配）
- [ ] Supabase（または Neon）プロジェクトと `DATABASE_URL`
- [ ] Render に `DATABASE_URL` / バックエンド切替フラグを設定
- [ ] 既存 Notion データのエクスポート権限（移行スクリプト用）

詳細な権限は [ONBOARDING](../ONBOARDING.md) に追記予定。

---

## 6. リスクと緩和
| リスク | 緩和 |
|---|---|
| 移行中のデータ不整合 | デュアルライト + 突合スクリプト + フラグで即時切戻し |
| スキーマ設計の手戻り | Phase 0 で Repository 抽象化し、DB 実装を差し替え可能に |
| ダウンタイム | 読込切替はフラグで段階的。Notion を残したまま並行運用 |

## 7. スコープ外（別Issue）
- フロントの Next.js 分離 / Vercel 化（DB移行後に検討）
- Redis / 専用ジョブキュー（まず `jobs` テーブルで十分）
