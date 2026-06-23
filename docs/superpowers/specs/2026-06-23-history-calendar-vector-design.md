# 設計: マッチング履歴 / カレンダー / ベクトル基盤（v2 追加）

**v1.0 | 2026-06-23**

v2 リビルド（[2026-06-22-rebuild-v2-design.md](./2026-06-22-rebuild-v2-design.md)）に 3 つの機能を追加する。
関連 Issue: 親 #16

## 決定事項（ブレストで合意）
- 埋め込み（embedding）: **Voyage AI（voyage-3 / 1024次元）** → **Supabase pgvector**
- カレンダー: **アプリ内カレンダー（MVP）**（外部連携は将来）

---

## E7. マッチング履歴

### 目的
スワイプ・つながり・商談結果を時系列で振り返れるようにする。これが E9 の「合う/合わない」分析の教師データにもなる。

### データ
- `swipes`（既存）: 興味あり/見送り＋日時 → スワイプ履歴
- `matches`（既存）: つながり成立＋日時
- **`match_outcomes`（新規）**: match に紐づく商談結果
  - `id, match_id, status('進行中'|'成立'|'継続検討'|'見送り'), note, recorded_at`

### 画面
- `/history`: タイムライン（種別フィルタ: スワイプ / つながり / 商談結果）
- つながり詳細から結果を記録（status 更新）

---

## E8. アプリ内カレンダー

### 目的
つながった企業との商談予定をアプリ内で作成・一覧する。

### データ
- **`calendar_events`（新規）**:
  - `id, company_id(自社), match_id(任意), title, start_at, end_at, location_or_url, note, created_at`

### 画面
- `/calendar`: 月表示 + 直近リスト
- つながり/履歴から「商談を予定する」→ イベント作成
- アプリ内リマインド（直近の予定をダッシュboardに表示）。外部通知は将来。

---

## E9. ベクトル基盤・資料保管・相性分析（中核）

### 9.1 資料の全保管
- アップロード資料（HP 本文・PDF）は `profile_sources` に **原本（Supabase Storage の `storage_path`）＋抽出テキスト（`extracted_text`）を消さずに保持**。
- プロフィール更新で素材を使っても、素材自体は履歴として残す（追記のみ）。

### 9.2 埋め込み（Voyage AI → pgvector）
- pgvector 拡張を有効化。
- 埋め込み対象と保存先:
  - `company_profiles.embedding vector(1024)` — summary/valueProp/strengths/challenges/targetMarket を結合して埋め込み
  - `profile_sources.embedding vector(1024)` — 各素材の抽出テキストを埋め込み
- 生成は **サーバ側**（`/api/embeddings`）で Voyage を呼ぶ。`VOYAGE_API_KEY` はサーバ専用。
- 生成タイミング: プロフィール保存時・素材アップロード時（非同期/オンデマンド）。
- モデル: `voyage-3`（1024次元）。`input_type` は document/query を使い分け。

### 9.3 意味的マッチング（ハイブリッド）
- 企業間のコサイン類似度を pgvector（`<=>`）で計算する SQL 関数 `match_companies(query_company_id, limit)`。
- 最終ランキング = **ルール親和性スコア（既存 scoring.ts）× α + ベクトル類似度 × β** のハイブリッド。
- ベクトルが未生成の企業はルールスコアのみで動作（グレースフル）。

### 9.4 「合う/合わない」分析
- ラベル: スワイプ（興味あり=合う / 見送り=合わない）、将来は match_outcomes も利用。
- **好みベクトル** = (合うと判定した企業 embedding の重心) − (合わないの重心)。
  - 新候補を「好みベクトルとの内積（=方向の一致度）」で再ランキング。
  - `preference_vectors`（新規・任意）に自社の好みベクトルをキャッシュ。
- 分析画面 `/insights`（叩き）:
  - 合う/合わない群の傾向（業種・規模・施策・意思決定スタイルの分布差）
  - 「あなたが惹かれる企業の特徴」をテキスト要約（Claude）
- 注意: データが少ないうちは統計的に弱い。件数しきい値未満では「サンプル不足」を明示。

### スキーマ追加（migrations）
- `0003_history_calendar.sql`: `match_outcomes`, `calendar_events`（+RLS）
- `0004_pgvector.sql`: `create extension vector`、`company_profiles.embedding` / `profile_sources.embedding`、`match_companies()` 関数、ivfflat インデックス

### 公開影響
- 追加環境変数: `VOYAGE_API_KEY`（サーバ側のみ）
- Supabase で pgvector 拡張を有効化

---

## 段階実装（このPRで着手する範囲）
- ✅ migrations（履歴/カレンダー/pgvector）— SQL 先行
- ✅ Voyage 埋め込み lib（`lib/voyage.ts`）＋ `/api/embeddings`（キー未設定時はスキップ）
- ✅ ハイブリッドランキング・好みベクトルの **純粋ロジック（TS）** ＋ 単体テスト
- ✅ `/history`・`/calendar`・`/insights` の UI（モックデータで動作）
- ⏳ 実 DB 連携・実埋め込み生成は Supabase/Voyage キー取得後（E1 実接続と合流）

## 非対象（将来）
- Google カレンダー連携 / 外部通知
- 大規模ベクトル検索の最適化（HNSW 等）、再ランキングの ML 化
