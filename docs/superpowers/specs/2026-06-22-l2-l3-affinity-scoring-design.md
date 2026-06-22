# 設計: レベル2/3 親和性スコアリング（叩き）

**v1.0 | 2026-06-22 | Blendy 協業マッチングシステム**

関連: [方向性ドキュメント](../../../ブレンディ　協業マッチング　方向性.md) / 前提PR: `refactor/directory-structure`（`src/blendy` パッケージ化）がマージ済み

---

## 1. 目的とスコープ

方向性ドキュメントが定義する「マッチング品質を決める3階層」のうち、未実装の
**レベル2（施策・種まき活動）** と **レベル3（性格・価値観・意思決定スタイル）** を
取り込む叩き（first cut）を作る。

- **Phase**: 方向性ドキュメントの推奨どおり **Phase 1 に集中**（Rule-based + 構造化質問）
- **動く範囲**: 既存の Notion ベースのマッチングフローに**加算層として統合**
- **非対象（Phase 2 以降）**: 自由記述テキストからの Claude 価値観抽出、成功率追跡（MATCHING_OUTCOME）

### ゴール / 受け入れ条件
- [ ] L2/L3 を構造化で取得する新フォーム `register_v3.html` と `/register-v3` 系エンドポイントが動く
- [ ] `affinity_scoring.py` の純粋関数群が `pytest` で全網羅テストされ通る
- [ ] `run_matching` に**既定OFFのフラグ**で加算層が差し込まれ、OFF時は既存挙動と完全一致
- [ ] スコア内訳（`AffinityBreakdown`）が結果に添付される
- [ ] 必要な Notion スキーマ変更が文書化されている（実DB変更は権限取得後）

---

## 2. アーキテクチャ

```
[ register_v3.html ] ──POST──> [ /api/register-v3 ]
   L1+L2+L3 入力                      │
                                      ▼
                          [ profile_schema.py ]  ← L1/L2/L3 を Pydantic で型定義
                                      │ MemberProfile
                                      ▼
                          [ notion_client ] ──> Notion（新フィールド保存）

[ run_matching ] ペア生成時:
   既存ルールスコア(L1)  +  [ affinity_scoring.py ](L2/L3 加算層, フラグ制御)
                                      │  AffinityBreakdown（内訳）
                                      ▼
                          総合スコア + スコア内訳 → 結果/ダッシュボード
```

### 新規モジュール（`src/blendy/` 配下・単一責務）
| モジュール | 責務 | 依存 |
|---|---|---|
| `profile_schema.py` | L1/L2/L3 のデータ構造を型定義（純粋） | Pydantic のみ |
| `affinity_scoring.py` | L2/L3 親和性スコアを純粋関数で算出・内訳を返す | profile_schema のみ |

### 変更する既存モジュール
- `matching_engine.py` — `run_matching` にフラグ付きで `affinity_scoring` を呼ぶ薄い結線を追加（OFF既定なら既存挙動と一致）
- `main.py` — `/register-v3`（フォーム表示）＋ `/api/register-v3`（登録）を追加
- `notion_client.py` — 新フィールドの save / parse を防御的に追加
- `config.py` — `ENABLE_AFFINITY_LAYER`（既定 `False`）, `SCORE_WEIGHTS_AFFINITY` を追加
- `templates/register_v3.html` — 新フォーム（新設）

**設計の肝**: L2/L3 ロジックを Notion/Claude 非依存の純粋モジュールに隔離し、
単体テスト可能にしつつ肥大化した `matching_engine.py` を汚さない。

---

## 3. データモデル（3階層の具体フィールド）

Phase 1 は **構造化質問のみ**（自由記述の Claude 採点は Phase 2 に予約）。

### レベル1（基本）— 既存
業務内容・業種・ターゲット市場。既存の `matching_engine` のルールスコア（100点）で評価済み。

### レベル2（施策・種まき活動）— 複数選択
`activities: list[str]`（キーワード集合として保存）

プリセット例（フォームのチェックボックス・自由追加可）:
- 交流会・ミートアップ参加 / 学生・大学コミュニティ活動 / 副事業・副次サービスへの投資
- 勉強会・セミナー登壇 / SNS・オンライン発信 / 紹介・リファラル活動

### レベル3（性格・価値観・意思決定スタイル）— select / Likert
| フィールド | 型 | 選択肢 | スコア方向 |
|---|---|---|---|
| `decision_style` 意思決定スタイル | enum | 即決派 / バランス型 / 慎重派 | **相補性**（即決↔慎重=高） |
| `time_horizon` 時間軸 | enum | 長期 / 中期 / 短期 | **親和性**（同じ=高） |
| `commitment_level` コミット度 | int(1–5) | Likert | **近さ**（差が小さいほど高） |
| `collaboration_style` 協調スタイル | enum | 個人主義 / バランス / 協調志向 | **親和性**（近い=高） |
| `past_collaboration` 協業経験 | enum | なし / 1–2回 / 3回以上 | **軽い加点** |
| `vision_text` ビジョン・こだわり | str | 自由記述 | **Phase 1 では保存のみ・非採点** |

**非対称な設計判断（方向性ドキュメントに忠実）:**
- 施策・時間軸・協調 = 揃うほど高得点（**類似性**）
- 意思決定スタイル = 逆ほど高得点（**相補性**。即決派×慎重派 = 成功パターン）
- ビジョン自由記述 = 保存するが採点しない（Phase 2 のフック）

---

## 4. スコアリングロジック

### 配点（既存 L1=100点 に対する加算層・上限50点）
```python
SCORE_WEIGHTS_AFFINITY = {
    "施策親和性(活動重複度)":  12,   # L2
    "意思決定スタイル相補性":  12,   # L3
    "価値観親和性(時間軸)":    10,   # L3
    "コミットレベル一致":       8,   # L3
    "協調スタイル親和性":       5,   # L3
    "協業経験ボーナス":         3,   # L3(軽)
}  # 合計 50
```

### 各次元の純粋関数（`affinity_scoring.py`）
| 関数 | レンジ | アルゴリズム |
|---|---|---|
| `score_activity_affinity(a, b)` | 0..12 | 施策セットの Jaccard 類似度 `|A∩B|/|A∪B|` × 12（両者空なら0） |
| `score_decision_complementarity(a, b)` | 0..12 | 即決=0,バランス=1,慎重=2 の順序距離。距離2で満点、0で0 → `distance/2*12` |
| `score_time_horizon_affinity(a, b)` | 0..10 | 同一=満点, 隣接=中(5), 両端=0 |
| `score_commitment_match(a, b)` | 0..8 | `clip(8 - |diff|*2, 0, 8)` |
| `score_collaboration_affinity(a, b)` | 0..5 | 同一=5, 隣接=2.5, 両端=0 |
| `score_past_collaboration_bonus(a, b)` | 0..3 | `max(level_a, level_b)` を 0 / 1.5 / 3 に写像 |

### 内訳の返却構造
```python
class AffinityItem(BaseModel):
    label: str          # "意思決定スタイル相補性"
    score: float        # 9.0
    max_score: float    # 12
    note: str           # "即決派 × 慎重派 → 相補的(高評価)"

class AffinityBreakdown(BaseModel):
    total: float                 # 加算層の合計(0..50)
    items: list[AffinityItem]
    reasons: list[str]           # 自動生成の「成功しそうな理由」文
```
合計でなく**内訳と理由文**を返すことで、方向性ドキュメント Week5-6
「スコア内訳」「成功しそうな理由の表示」の土台を先取りする。

### `run_matching` への結線（フラグ制御・既定OFF）
```python
base = existing_rule_score(a, b)            # 既存 L1 ロジック（不変）
if ENABLE_AFFINITY_LAYER:                    # config フラグ。OFF なら既存と完全一致
    bd = compute_affinity(a, b)              # affinity_scoring
    total = base + bd.total
    pair["score_breakdown"] = bd.dict()      # 結果に内訳を添付
else:
    total = base
```

### エラーハンドリング
- L2/L3 欠損（旧フォーム経由のメンバー）→ 各関数は**中立スコア0で継続**、例外を投げない。
- `compute_affinity` は片方でも欠損なら欠損次元を0点としつつ内訳に「データ不足」と明記。

---

## 5. テスト戦略

`tests/test_affinity_scoring.py`（純粋関数なのでライブ依存なしで全網羅）:
- 各次元の境界値: 施策 空/完全一致/部分一致、意思決定 即決×慎重(満点)/同一(0)、
  時間軸 同一/両端、コミット 差0/差4、協調 同一/両端、協業経験 各レベル
- 欠損フィールド → 例外なし・0継続
- 不変条件: `total ∈ [0,50]`、各 `item.score ≤ item.max_score`
- `profile_schema` バリデーション（Likert 範囲外・不正 enum）

既存テスト（`tests/`）は不変。`ENABLE_AFFINITY_LAYER=False` 既定により
`run_matching` の回帰はないことを確認する。

---

## 6. 必要な Notion スキーマ変更（権限取得後に実施）

実DB変更はクレデンシャル取得後（[ONBOARDING](../../ONBOARDING.md) 参照）。コードは
フィールド未定義でも落ちないよう防御的に実装する。

- **MEMBERS_DB**: `施策活動`(multi-select), `意思決定スタイル`(select), `時間軸`(select),
  `コミットレベル`(number), `協調スタイル`(select), `協業経験`(select), `ビジョン記述`(rich_text)
- **MATCHING_RESULTS_DB**: `スコア内訳`(rich_text に JSON 文字列)

---

## 7. 叩きとして「未完了」を明示する範囲
- ビジョン自由記述の **Claude 価値観抽出（Phase 2）** は器のみ・未採点
- `ENABLE_AFFINITY_LAYER` 既定 **False**（本番無影響）。有効化＋Notion スキーマ反映は別タスク
- 成功率追跡（MATCHING_OUTCOME / Week 7-8）はスコープ外
- 配点・重みは初期値（叩き）。実データでの調整を前提とする
