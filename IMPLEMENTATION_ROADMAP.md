# マルチアクティビティ対応 実装ロードマップ

## 📋 概要

新しいマルチアクティビティ型フォーム（`register_multiactivity.html`）と スコアリングロジック（`matching_engine_multiactivity.py`）の統合を段階的に実施します。

### 影響を受けるファイル一覧

| ファイル | 現状 | 変更内容 | 優先度 |
|---------|------|--------|--------|
| `main.py` | `/api/register` で FormData 処理 | マルチアクティビティ対応に修正 | 🔴 必須 |
| `notion_client.py` | member DB のみ操作 | activities テーブル対応追加 | 🔴 必須 |
| `templates/register_new.html` | 単一アクティビティ | → `register_multiactivity.html` に置き換え | 🟡 段階的 |
| `matching_engine.py` | 単一スコアリング | → `matching_engine_multiactivity.py` を統合 | 🟡 段階的 |
| `config.py` | DB ID 定義 | activities テーブル ID 追加 | 🔴 必須 |
| `render.yaml` | Notion API キーのみ | 変更なし（DB ID は config.py で管理） | ✅ 不要 |

---

## 🚀 Phase 1: バックエンド準備（1-2日）

### タスク 1-1: Notion に activities テーブル作成

**やることリスト：**

1. Notion ダッシュボードで新規データベース作成
   - テーブル名：`activities`
   - 関連するメンバーDB：members DB ID = "517b9ae4-8e9d-496d-b581-927bde2af2fe"

2. スキーマ定義

```
フィールド名          | 型              | 説明
-------------------|-----------------|---------
ID                 | 自動採番         | 一意識別子
member_id          | Relation        | members DB への参照（1対多）
アクティビティ名     | Text (title)   | 例：人材紹介、交流会、コンサル
サービス内容        | Text            | 詳細な説明
強み_キーワード     | Multi-select   | 技術・開発、営業・ネットワーク等
強み_詳細          | Text            | 自由記述
課題_キーワード     | Multi-select   | 営業・マーケティング、リソース等
課題_詳細          | Text            | 自由記述
バリューチェーン位置 | Multi-select   | 営業・提案、開発・導入等
対象業界           | Text            | カンマ区切り：「製造業、金融業」
対象企業規模       | Select          | 個人・フリーランス / スモール〜10名 / 中小企業10〜300名 / 大企業300名〜
作成日時           | Created time    | 自動設定
更新日時           | Last edited time | 自動設定
```

3. members DB との Relation を設定
   - members テーブルに「activities」フィールド追加（Relation: 1対多）

### タスク 1-2: config.py に ACTIVITIES_DB_ID 追加

```python
# config.py

# Notion DB IDs
MEMBERS_DB_ID = os.getenv("MEMBERS_DB_ID", "517b9ae4-8e9d-496d-b581-927bde2af2fe")
ACTIVITIES_DB_ID = os.getenv("ACTIVITIES_DB_ID", "[新規作成した activities DB の ID]")
MATCHING_HISTORY_DB_ID = os.getenv("MATCHING_HISTORY_DB_ID", "...")
MATCHING_RESULTS_DB_ID = os.getenv("MATCHING_RESULTS_DB_ID", "...")
UNMATCHED_MEMBERS_DB_ID = os.getenv("UNMATCHED_MEMBERS_DB_ID", "...")

# スコアリング設定
MIN_SCORE = int(os.getenv("MIN_SCORE", "45"))
```

### タスク 1-3: notion_client.py に活動管理関数を追加

```python
# notion_client.py に追加

def create_activity(member_id: str, activity_data: dict) -> dict:
    """
    Notion の activities テーブルに活動を記録

    Args:
        member_id: members テーブルのレコード ID
        activity_data: {
            'アクティビティ名': str,
            'サービス内容': str,
            '強み_キーワード': list,
            '強み_詳細': str,
            '課題_キーワード': list,
            '課題_詳細': str,
            'バリューチェーン位置': list,
            '対象業界': str,
            '対象企業規模': str,
        }

    Returns:
        created activity record
    """
    payload = {
        "parent": {"database_id": ACTIVITIES_DB_ID},
        "properties": {
            "member_id": {"relation": [{"id": member_id}]},
            "アクティビティ名": {"title": [{"text": {"content": activity_data['アクティビティ名']}}]},
            "サービス内容": {"rich_text": [{"text": {"content": activity_data['サービス内容']}}]},
            "強み_キーワード": {"multi_select": [{"name": kw} for kw in activity_data['強み_キーワード']]},
            "強み_詳細": {"rich_text": [{"text": {"content": activity_data['強み_詳細']}}]},
            # ... 他のフィールドも同様
        }
    }
    res = requests.post(NOTION_API_URL + "/pages", headers=HEADERS, json=payload, timeout=10)
    res.raise_for_status()
    return res.json()


def get_member_activities(member_id: str) -> list:
    """
    特定のメンバーの全活動を取得
    """
    payload = {
        "filter": {
            "property": "member_id",
            "relation": {"contains": member_id}
        },
        "page_size": 100
    }
    res = requests.post(
        NOTION_API_URL + f"/databases/{ACTIVITIES_DB_ID}/query",
        headers=HEADERS,
        json=payload,
        timeout=10
    )
    res.raise_for_status()
    results = res.json()['results']
    
    activities = []
    for r in results:
        activities.append({
            'id': r['id'],
            'アクティビティ名': _text(r['properties'], 'アクティビティ名'),
            'サービス内容': _text(r['properties'], 'サービス内容'),
            # ... 他のフィールドも抽出
        })
    
    return activities
```

---

## 🚀 Phase 2: フロントエンド移行（1-2日）

### タスク 2-1: フォーム切り替え

```python
# main.py

@app.get("/register")
async def get_register_form():
    """フォーム画面を返す"""
    # 新フォームに切り替え
    return FileResponse("templates/register_multiactivity.html")

# 既存の route も互換性のために残す
@app.get("/register-old")
async def get_register_form_old():
    """旧フォーム（互換性保持）"""
    return FileResponse("templates/register_new.html")
```

### タスク 2-2: FormData パースロジック更新

```python
# main.py の /api/register エンドポイント

@app.post("/api/register")
async def register(request: Request):
    """
    マルチアクティビティ対応フォーム受け取り
    """
    form = await request.form()

    try:
        # 基本情報
        member_data = {
            '名前': form.get('名前'),
            '会社名': form.get('会社名'),
            '業種カテゴリ': form.get('業種カテゴリ'),
            '業種詳細': form.get('業種詳細'),
            '事業フェーズ': form.get('事業フェーズ'),
            'メール': form.get('メール'),
            'LINE_ID': form.get('LINE_ID', ''),
            'Facebook_URL': form.get('Facebook_URL', ''),
        }

        # members DB に登録
        member_record = notion_client.create_member(member_data)
        member_id = member_record['id']

        # アクティビティを解析（複数）
        for activity_num in [1, 2, 3]:
            activity_name = form.get(f'活動{activity_num}_名称')
            
            # 空でなければ記録
            if activity_name and activity_name.strip():
                activity_data = {
                    'アクティビティ名': activity_name,
                    'サービス内容': form.get(f'活動{activity_num}_サービス', ''),
                    '強み_キーワード': form.getlist(f'活動{activity_num}_強み'),
                    '強み_詳細': form.get(f'活動{activity_num}_強み詳細', ''),
                    '課題_キーワード': form.getlist(f'活動{activity_num}_課題'),
                    '課題_詳細': form.get(f'活動{activity_num}_課題詳細', ''),
                    'バリューチェーン位置': form.getlist(f'活動{activity_num}_ポジション'),
                    '対象業界': form.get(f'活動{activity_num}_対象業界', ''),
                    '対象企業規模': form.get(f'活動{activity_num}_対象規模', ''),
                }
                
                # activities DB に記録
                notion_client.create_activity(member_id, activity_data)

        return {"success": True, "member_id": member_id}

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return {"success": False, "error": "登録に失敗しました"}
```

---

## 🚀 Phase 3: マッチングロジック統合（2-3日）

### タスク 3-1: matching_engine.py を multiactivity 版に統合

**方針：バージョニングアプローチ**

```python
# matching_engine.py（既存）と matching_engine_multiactivity.py を統合

# オプション A: 条件分岐で両対応
def score_pair(member_a: dict, member_b: dict) -> dict:
    """
    互換性を保持しつつ、マルチアクティビティに対応
    """
    
    # member_a, member_b にアクティビティ情報があるか判定
    if 'activities' in member_a and len(member_a['activities']) > 1:
        # マルチアクティビティロジック
        return score_pair_multiactivity(member_a, member_b)
    else:
        # 従来のシングルアクティビティロジック
        return score_pair_single(member_a, member_b)
```

### タスク 3-2: run_matching() を更新

```python
# matching_engine.py の run_matching()

def run_matching(members: List[dict], ...) -> List[dict]:
    """
    マルチアクティビティ対応のマッチング実行
    """
    
    results = []

    for member_a, member_b in itertools.combinations(members, 2):
        # アクティビティ情報を取得
        activities_a = notion_client.get_member_activities(member_a['id'])
        activities_b = notion_client.get_member_activities(member_b['id'])

        member_a['activities'] = activities_a
        member_b['activities'] = activities_b

        # スコア計算（自動的にマルチアクティビティ対応）
        score = score_pair(member_a, member_b)

        if score['total'] >= MIN_SCORE:
            results.append({
                'メンバーA': member_a['会社名'],
                'メンバーB': member_b['会社名'],
                'スコア': score['total'],
                'マッチパターン数': len(score.get('all_matches', [])),
                'プライマリマッチ': score.get('primary_match'),
                '説明': score.get('justification', ''),
            })

    # ソート＆1人1組制限
    results.sort(key=lambda x: -x['スコア'])
    return apply_one_person_one_match_constraint(results)
```

### タスク 3-3: テスト実行

```bash
# matching_engine_multiactivity.py のテストを実行
python matching_engine_multiactivity.py

# 出力：
# === マッチング結果 ===
# 人材紹介会社A (田中太郎) × マーケティング会社B (山田花子)
#   スコア: 72
#   協業タイプ: A型
#   マッチパターン数: 2
#   プライマリマッチ: ('人材紹介', 'Webマーケティング')
#   説明: 2個のマッチパターン検出。最高スコア: 人材紹介 × Webマーケティング = 72
```

---

## 🚀 Phase 4: 既存ユーザー対応（1-2日）

### タスク 4-1: 既存データのマイグレーション

```python
# migration_script.py

def migrate_single_to_multi_activity():
    """
    既存メンバー（単一アクティビティ）をマルチアクティビティ化
    
    「主力サービス」「バリューチェーン位置」などが
    活動1（Activity 1）として activities テーブルに登録される
    """
    
    all_members = notion_client.get_all_members()
    
    for member in all_members:
        # すでにアクティビティが作成されていないか確認
        existing_activities = notion_client.get_member_activities(member['id'])
        
        if len(existing_activities) == 0:
            # シングルアクティビティを Activity 1 に変換
            activity_data = {
                'アクティビティ名': member['業種詳細'],  # 例：「SaaS開発」
                'サービス内容': member['主力サービス'],
                '強み_キーワード': member['強み_キーワード'],
                '強み_詳細': member['強み'],
                '課題_キーワード': member['課題_キーワード'],
                '課題_詳細': member['課題足りないもの'],
                'バリューチェーン位置': member['バリューチェーン位置'],
                '対象業界': member['エンドクライアント業界'],
                '対象企業規模': member['エンドクライアント規模'],
            }
            
            notion_client.create_activity(member['id'], activity_data)
            print(f"✅ {member['会社名']} を移行完了")
```

### タスク 4-2: 既存ユーザーへの案内送信（LINE/Email）

メッセージ例：

> 📢 ブレンドマッチ からのお知らせ
>
> いつもご利用ありがとうございます！
>
> 📌 **新機能：複数事業の登録に対応しました**
>
> 貴社が複数の事業活動を展開している場合（例：営業代行 + イベント企画）、それぞれを個別に登録することで、**より精密なマッチングが可能**になりました。
>
> 📝 **マッチング精度向上例**
> - 人材紹介会社：「人材紹介」と「交流会主催」をそれぞれ登録
> - その結果、営業支援企業とマーケティング企業の両方とマッチ可能に！
>
> ぜひこの機会に、プロフィールを更新してください。
> > [プロフィール更新へ](https://localhost:8000/register)
>
> ご質問はお気軽にお問い合わせください。

---

## 🚀 Phase 5: 検証・デプロイ（1-2日）

### タスク 5-1: ローカルテスト

```bash
# 1. ローカルで dev サーバー起動
npm run dev  # またはフロント
python main.py  # バックエンド

# 2. 新フォームで複数アクティビティを登録
# → register_multiactivity.html で人材紹介 + 交流会を入力

# 3. Notion DB に正しく記録されたか確認
# → members テーブルとactivities テーブル両方を確認

# 4. マッチング実行
curl -X POST http://localhost:8000/api/run-matching

# 5. 結果確認
# → マッチパターン数が複数表示されるか
# → スコアが向上しているか
```

### タスク 5-2: 本番環境デプロイ（Render.com）

1. GitHub にコミット
   ```bash
   git add .
   git commit -m "feat: マルチアクティビティ対応フォーム・マッチングロジック実装

   - register_multiactivity.html: 最大3アクティビティを同時登録
   - matching_engine.py: アクティビティペア単位でのスコアリング
   - notion_client.py: activities テーブル対応

   既存ユーザーは自動的にシングルアクティビティモデルで継続利用可能"
   ```

2. Render.com にデプロイ
   ```bash
   git push origin main
   # Render が自動デプロイを実行
   ```

3. 本番環境で検証
   ```bash
   curl https://blendy-matching.onrender.com/register
   # マルチアクティビティフォームが表示されるか確認
   ```

---

## 📊 期待される効果

### マッチング精度向上

| ケース | 改善前 | 改善後 |
|--------|--------|---------|
| 人材紹介 vs. マーケティング | 1パターン（営業支援型のみ） | 2パターン（営業支援型 + PR型） |
| 複数業界向けコンサル | 業界別マッチ不可 | 業界別の最適パートナー発見可能 |
| キャパシティ補完 | 企業全体で評価（雑） | アクティビティ単位で評価（精密） |

### ビジネスインパクト

- **成約率向上**: アクティビティレベルの細かいマッチ → 対等性判定の精度向上
- **顧客満足度向上**: 「こんなパートナーを探していた！」のマッチ増加
- **複業企業対応**: 複数事業を展開している企業をより正確に評価可能

---

## 🔧 トラブルシューティング

### Q: FormData で複数アクティビティを正しく受け取れない

A: JavaScriptで `form.getlist('活動2_課題')` のような形式で複数値を取得すること。
   HTML のチェックボックスは全て同じ name でないと複数値が渡されません。

### Q: 既存ユーザーのマッチング結果が変わってしまった

A: これは期待動作です。アクティビティ情報が自動登録されたため、スコアリングがより精密になります。
   既存マッチ履歴の重複チェック（frozenset）により、再マッチは防止されます。

### Q: Notion API エラーが多発

A: `notion_client.py` に リトライロジック（tenacity）を追加します。
   詳細は Phase 1 の本番化実装計画（SECURITY ENHANCEMENT）を参照。

---

## 📝 チェックリスト

- [ ] Notion で activities テーブル作成
- [ ] ACTIVITIES_DB_ID を config.py に追加
- [ ] notion_client.py に create_activity(), get_member_activities() 追加
- [ ] register_multiactivity.html をデプロイ
- [ ] /api/register を マルチアクティビティ対応に更新
- [ ] matching_engine_multiactivity.py を既存エンジンに統合
- [ ] 既存ユーザーデータを移行
- [ ] ローカルテスト実行＆検証
- [ ] 本番デプロイ
- [ ] 既存ユーザーへ案内メール送信

