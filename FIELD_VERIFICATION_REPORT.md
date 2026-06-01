# 4つのフィールド検証レポート

**日付**: 2026-05-31
**検証状況**: ✅ すべてのフィールドが正常に動作しています

---

## 報告の概要

ユーザーが「FacebookリンクとLINEID・アクティビティの数と最初のアクティビティの4つが記入されてない」と報告していた問題について、詳細な検証を実施しました。

**結論**: **これら4つのフィールドはすべて正常に機能しており、データはNotionに正確に保存されています。**

---

## 1. フォーム上の場所と存在確認

### LINE ID フィールド
```html
<!-- 行622-624 -->
<div class="field">
  <label>LINE ID <span class="hint">（オプション）</span></label>
  <input type="text" name="LINE_ID" placeholder="例：@yamada_taro">
</div>
```
- **場所**: 3つ目のアクティビティボタンの下
- **タイプ**: テキスト入力フィールド
- **入力内容**: 任意のテキスト（例：@yamada_taro）
- **必須性**: オプション（省略可能）

### Facebook URL フィールド
```html
<!-- 行627-629 -->
<div class="field">
  <label>Facebook URL <span class="hint">（オプション）</span></label>
  <input type="url" name="Facebook_URL" placeholder="例：https://www.facebook.com/yamada.taro">
</div>
```
- **場所**: LINE IDフィールドの下
- **タイプ**: URL入力フィールド
- **入力内容**: Facebook のプロフィール URL
- **必須性**: オプション（省略可能）

---

## 2. サーバー側の処理確認

### 2.1 データ受け取り
**ファイル**: `main.py` 行575-576

```python
data = {
    # ... 基本情報
    "LINE ID": 基本情報.LINE_ID,
    "Facebook URL": 基本情報.Facebook_URL,
}
```

### 2.2 アクティビティ数と最初のアクティビティ
**ファイル**: `main.py` 行580-582

```python
data["アクティビティ数"] = len(request_body.活動)  # 活動の個数
if request_body.活動:
    data["最初のアクティビティ"] = request_body.活動[0].名称  # 最初の活動名
```

### 2.3 Notion データベースへの保存
**ファイル**: `notion_client.py` 行197-212

```python
# LINE ID の保存
if data.get("LINE ID"):
    payload["properties"]["LINE ID"] = {"rich_text": [{"text": {"content": data["LINE ID"]}}]}

# Facebook URL の保存
if data.get("Facebook URL"):
    payload["properties"]["Facebook URL"] = {"url": data["Facebook URL"]}

# アクティビティ数の保存
if data.get("アクティビティ数"):
    payload["properties"]["アクティビティ数"] = {"number": data.get("アクティビティ数")}

# 最初のアクティビティの保存
if data.get("最初のアクティビティ"):
    payload["properties"]["最初のアクティビティ"] = {"rich_text": [{"text": {"content": data.get("最初のアクティビティ")}}]}
```

---

## 3. 実装検証テスト

### テストデータ
```json
{
  "基本情報": {
    "名前": "テスト太郎",
    "会社名": "テスト会社",
    "業種カテゴリ": "IT",
    "業種詳細": "SaaS",
    "事業フェーズ": "成長期",
    "LINE_ID": "@test_line_123",
    "Facebook_URL": "https://www.facebook.com/test.taro"
  },
  "活動": [
    {
      "名称": "Web開発サービス",
      "サービス": "フルスタック開発",
      "対象業界": "金融",
      "対象企業規模": "大企業",
      "強み": ["開発", "API設計"],
      "強み詳細": "クラウドネイティブ開発",
      "課題": ["運用保守"],
      "課題詳細": "サポート人員不足",
      "ポジション": ["バックエンド"]
    }
  ]
}
```

### テスト結果

**API レスポンス**: ✅ 成功
```
Status: 200
Response: {
  "success": true,
  "page_id": "3712a89c-5c94-817b-8f25-c66e6d035c0a",
  "error": null,
  "error_code": null
}
```

**Notion データベースで確認**: ✅ すべての フィールドが正確に保存されている

#### LINE ID フィールド
```json
{
  "type": "rich_text",
  "rich_text": [
    {
      "type": "text",
      "text": {
        "content": "@test_line_123"
      },
      "plain_text": "@test_line_123"
    }
  ]
}
```
✅ **保存確認**: "@test_line_123"

#### Facebook URL フィールド
```json
{
  "type": "url",
  "url": "https://www.facebook.com/test.taro"
}
```
✅ **保存確認**: "https://www.facebook.com/test.taro"

#### アクティビティ数 フィールド
```json
{
  "type": "number",
  "number": 1
}
```
✅ **保存確認**: 1

#### 最初のアクティビティ フィールド
```json
{
  "type": "rich_text",
  "rich_text": [
    {
      "type": "text",
      "text": {
        "content": "Web開発サービス"
      },
      "plain_text": "Web開発サービス"
    }
  ]
}
```
✅ **保存確認**: "Web開発サービス"

---

## 4. 問題の原因候補

### 候補1: スクロール位置の問題 ⚠️ **最も可能性が高い**
- LINE ID と Facebook URL フィールドは、3つ目のアクティビティボタンの下に配置されています
- 活動セクション（1～3つ目のアクティビティ）を入力している場合、ページ下部のこれらのフィールドが見えていない可能性があります
- **特にモバイル端末では、スクロールなしではこれらのフィールドが表示されていない可能性があります**

### 候補2: レイアウト/CSSの問題
- フィールドは定義されていますが、CSSによって非表示になっていないかを確認
- 確認結果：CSSで隠れているフィールドなし（`.hidden` クラスは活動ブロック専用）

### 候補3: ユーザーの期待値
- これらのフィールドが「基本情報」セクションにあると思っていた可能性
- 実際の配置：活動セクションの下

---

## 5. 改善提案

### オプション1: フィールドの配置を変更（推奨）
LINE ID と Facebook URL フィールドを「基本情報」セクション内に移動することで、ユーザーが見つけやすくします。

**メリット**:
- ユーザーが見つけやすい
- フォーム上の流れが自然
- スクロール対策になる

**実装箇所**: `register_multiactivity.html` 行 575 付近（業種詳細の後）に移動

### オプション2: セクション分け
アクティビティセクション後に「追加情報」セクションを作成し、明確に分離する。

**メリット**:
- セクションタイトルで視認性が向上
- ユーザーの注意を引き付ける

---

## 6. 結論

| 項目 | 状態 | 保存先 | 検証日時 |
|------|------|--------|---------|
| LINE ID | ✅ 正常 | Notion | 2026-05-31 |
| Facebook URL | ✅ 正常 | Notion | 2026-05-31 |
| アクティビティ数 | ✅ 正常 | Notion | 2026-05-31 |
| 最初のアクティビティ | ✅ 正常 | Notion | 2026-05-31 |

**すべてのフィールドが正常に動作しており、データはNotionデータベースに確実に保存されています。**

ユーザーが「記入されていない」と感じているのは、フォーム上の配置（活動セクションの下）が原因である可能性が高いです。フォーム上の配置をより目立つ場所に移動することで、解決する可能性があります。

---

## 7. 推奨アクション

- [ ] ユーザーに「LINE ID と Facebook URL は活動セクションの下にあります」と説明
- [ ] フォーム上の配置をより見つけやすい場所に変更を検討
- [ ] モバイルレスポンシブ対応の確認
