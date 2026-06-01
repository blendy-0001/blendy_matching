# 🔄 マッチング結果のバックアップ・復元ガイド

誤削除や万が一のトラブルに備えて、マッチング結果をバックアップする方法をまとめました。

---

## 📋 目次
1. [Notionの復元機能](#1-notionの復元機能)
2. [プログラム側でのバックアップ](#2-プログラム側でのバックアップ)
3. [定期バックアップの自動化](#3-定期バックアップの自動化)
4. [復元手順](#4-復元手順)
5. [トラブルシューティング](#5-トラブルシューティング)

---

## 1. Notionの復元機能

### ✅ ゴミ箱から復元

Notionでは**削除後30日間、ゴミ箱に保存**されます。

**復元手順：**
```
1. Notionワークスペース左下 → 「ゴミ箱」をクリック
2. 削除されたページ・レコードを検索
3. 対象を選択 → 「復元」をクリック
4. 元のデータベースに戻ります
```

**注意：** 30日を超えると完全削除されます

### ✅ バージョン履歴で過去の状態を確認

Notionのページには**自動的に編集履歴が保存**されます。

**確認手順：**
```
1. 対象のページを開く
2. 右上の「•••」 → 「バージョン履歴」をクリック
3. 過去のスナップショットを日時で確認
4. 「このバージョンを復元」で元に戻します
```

**利点：** 1つのレコードの過去編集内容が全て保存される

---

## 2. プログラム側でのバックアップ

Notionのみに依存せず、**ローカルにもバックアップを保存する**ことをお勧めします。

### 📁 バックアップファイルの自動生成

マッチング実行時に、結果をJSON形式でローカルに保存します。

**保存場所：**
```
C:\Users\yo_yo\Documents\blendy_matching\backups\
└─ matching_results_2026-05-23_session1.json
└─ matching_results_2026-05-23_session2.json
└─ matching_results_2026-06-01_session1.json
（日付_セッション番号で管理）
```

### 🔧 実装方法

`matching_engine.py` に以下の関数を追加：

```python
import json
import os
from datetime import datetime

def save_backup(matches: list[dict], session_name: str):
    """マッチング結果をバックアップファイルに保存"""
    
    # backups ディレクトリを確保
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # ファイル名：日付_セッション番号
    timestamp = datetime.now().strftime("%Y-%m-%d")
    session_counter = 1
    while True:
        filename = f"matching_results_{timestamp}_session{session_counter}.json"
        filepath = os.path.join(backup_dir, filename)
        if not os.path.exists(filepath):
            break
        session_counter += 1
    
    # マッチング結果をJSONで保存
    backup_data = {
        "session_name": session_name,
        "timestamp": datetime.now().isoformat(),
        "total_matches": len(matches),
        "matches": matches
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ バックアップ保存: {filepath}")
    return filepath
```

### 📝 使い方

`main.py` の中で、マッチング実行後に以下を追加：

```python
from matching_engine import run_matching, save_backup

# マッチング実行
matches = run_matching(members, matched_pairs)

# Notionに保存
for match in matches:
    notion_client.save_matching_result(session_name, match)

# ローカルにもバックアップ保存 👈 追加
backup_path = save_backup(matches, session_name)
print(f"復元用バックアップ: {backup_path}")
```

---

## 3. 定期バックアップの自動化

毎月のマッチング実行時に自動的にバックアップを取ることをお勧めします。

### 📅 スケジュール例

```
【毎月 1日と 15日】
├─ AM 9:00 - AI マッチング実行
├─ AM 9:30 - ローカルバックアップ自動保存
├─ AM 10:00 - あなたが Notion で確認・修正
└─ 昼間に   - あなたが相手に連絡（テンプレート使用）
```

### 🔧 自動バックアップの設定

タスクスケジューラーや cron ジョブで定期実行：

```bash
# Linux/Mac の cron
0 9 1,15 * * cd /path/to/blendy_matching && python main.py --backup

# Windows のタスクスケジューラー
python C:\Users\yo_yo\Documents\blendy_matching\main.py --backup
```

---

## 4. 復元手順

### 🆘 「誤ってNotionのデータを削除してしまった！」

**手順1：Notionのゴミ箱を確認**
```
1. Notionワークスペース左下 → 「ゴミ箱」
2. 削除したページ/レコードを検索
3. 復元ボタンをクリック
```

**手順2：それでも見つからない場合、ローカルバックアップから復元**
```
1. backups フォルダを開く
2. 対象の日付のファイルを探す
   例：matching_results_2026-05-23_session1.json
3. このファイルをテキストエディタで開く
4. マッチング情報を確認
```

**手順3：Notionに手動で再入力（または API で再作成）**
```python
import json
from notion_client import create_member, save_matching_result

# バックアップから読み込み
with open('backups/matching_results_2026-05-23_session1.json') as f:
    backup_data = json.load(f)

# Notion に再度保存
for match in backup_data['matches']:
    save_matching_result(session_name, match)
    print(f"復元: {match['メンバーA名']} × {match['メンバーB名']}")
```

---

## 5. トラブルシューティング

### ❓ Q1. バックアップファイルはどこにある？
**A.** `C:\Users\yo_yo\Documents\blendy_matching\backups\` フォルダを開いてください。

### ❓ Q2. 古いバックアップは削除してもいい？
**A.** 3ヶ月以上前のファイルは削除してもOKです。ただし、成約事例については保存しておくと良いです。

### ❓ Q3. Notionの30日以上前の削除データは復元できない？
**A.** Notionのゴミ箱では不可。ただしローカルバックアップがあれば復元可能です（このシステムを使用している場合）。

### ❓ Q4. バックアップファイルが破損した場合は？
**A.** JSON ファイルを別のテキストエディタで開いて、手動で編集できます。または、Notion の「バージョン履歴」で過去の状態を確認してください。

---

## 💡 ベストプラクティス

### ✅ やるべきこと
- ✅ 毎月のマッチング実行時にバックアップを取る
- ✅ 3ヶ月ごとに外付けハードディブに複製を保存
- ✅ 誤削除に気づいたら、すぐに「ゴミ箱」を確認（30日以内）
- ✅ 重要な成約事例は手元に記録

### ❌ やらないこと
- ❌ バックアップなしに、Notionのレコードを大量削除
- ❌ 30日以上、ゴミ箱を放置
- ❌ 外付けドライブなしで、ローカルファイルのみに依存

---

## 📊 バックアップの状態確認

以下のコマンドでバックアップ状態を確認：

```bash
# backups フォルダを一覧表示
ls -lh backups/

# 最新のバックアップを確認
ls -lt backups/ | head -5

# ファイルサイズを確認
du -h backups/
```

---

**最終更新：2026-05-23**  
**推奨：バックアップ機能の早期導入**

