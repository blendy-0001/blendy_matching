# archive/

本番アプリケーションが依存しない、参照用の旧コード・一時成果物を保管しています。

- `legacy_tests/` — ルート直下にあった、ライブ API を叩くアドホックな検証スクリプト群（正式な pytest スイートは `tests/`）
- `matching_engine_multiactivity.py` — どこからも import されていない旧マッチングエンジン
- `register*.html` — `templates/` の旧フォーム（現行は `register_multiactivity.html`）
- `*.json` / `*.txt` — 過去の実行結果・スキーマダンプなどの一時成果物

> ⚠️ ここのファイルは本番デプロイ（`render.yaml` の起動対象 `src/blendy`）には含まれません。
