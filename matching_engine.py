"""
AIマッチングエンジン
Claude APIを使って全ペアをスコアリングし、最適なマッチングを生成する
"""
import json
import itertools
import anthropic
from config import CLAUDE_API_KEY, MIN_SCORE, MAX_MATCHES_PER_RUN, COLLABORATION_TYPES

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def run_matching(members: list[dict], matched_pairs: set[frozenset]) -> list[dict]:
    """
    メインのマッチング処理
    1. 全ペアを生成（再マッチング除外）
    2. AIでスコアリング
    3. 上位ペアを選定して紹介文を生成
    """
    # ── Step1: 有効なペアを生成 ──────────────────
    valid_pairs = []
    for a, b in itertools.combinations(members, 2):
        pair_key = frozenset([a["名前"], b["名前"]])
        if pair_key not in matched_pairs:
            valid_pairs.append((a, b))

    if not valid_pairs:
        return []

    # ── Step2: AIでスコアリング ───────────────────
    print(f"  → {len(valid_pairs)}組をスコアリング中...")
    scored = []
    for a, b in valid_pairs:
        result = _score_pair(a, b)
        if result and result["スコア"] >= MIN_SCORE:
            scored.append(result)

    # スコア降順でソート
    scored.sort(key=lambda x: x["スコア"], reverse=True)

    # ── Step3: 上位ペアを選定（1人が複数回選ばれすぎないよう調整）──
    selected = _select_balanced_pairs(scored, MAX_MATCHES_PER_RUN)

    # ── Step4: 紹介文を生成 ──────────────────────
    print(f"  → {len(selected)}組の紹介文を生成中...")
    for match in selected:
        match["紹介文"] = _generate_intro(match)

    return selected


def _score_pair(a: dict, b: dict) -> dict | None:
    """Claude APIで1ペアをスコアリング"""
    prompt = f"""
あなたは協業マッチングの専門AIです。
以下の2人のビジネスプロフィールを分析し、協業の可能性をスコアリングしてください。

## メンバーA: {a['名前']}
- 業種: {a['業種カテゴリ']} / {a['業種詳細']}
- 主力サービス: {a['主力サービス']}
- エンドクライアントの業界: {a['エンドクライアント業界']}
- エンドクライアントの規模: {a['エンドクライアント規模']}
- クライアントの課題: {a['クライアントの課題']}
- バリューチェーン上の位置: {', '.join(a['バリューチェーン位置'])}
- 強み: {a['強み']}
- 課題・足りないもの: {a['課題・足りないもの']}
- 保有アセット: {', '.join(a['保有アセット'])}
- 事業フェーズ: {a['事業フェーズ']}

## メンバーB: {b['名前']}
- 業種: {b['業種カテゴリ']} / {b['業種詳細']}
- 主力サービス: {b['主力サービス']}
- エンドクライアントの業界: {b['エンドクライアント業界']}
- エンドクライアントの規模: {b['エンドクライアント規模']}
- クライアントの課題: {b['クライアントの課題']}
- バリューチェーン上の位置: {', '.join(b['バリューチェーン位置'])}
- 強み: {b['強み']}
- 課題・足りないもの: {b['課題・足りないもの']}
- 保有アセット: {', '.join(b['保有アセット'])}
- 事業フェーズ: {b['事業フェーズ']}

## スコアリング基準（合計100点）
1. エンドクライアント一致度（30点）
   - 同じ業界・規模・課題感のクライアントにサービスを提供しているか

2. バリューチェーン接続性（25点）
   - 前後工程でつながるか（1つ隣=25点、2つ隣=15点、同じ工程=0点、競合=-10点）

3. 市場ソリューションフィット（25点）
   - 一方がソリューション（技術・ノウハウ）、他方が市場（顧客基盤・チャネル）を持つか

4. 事業拡張ポテンシャル（20点）
   - 協業によって新市場・新顧客・新サービスが生まれる可能性があるか

## 協業タイプ（該当するものをすべて選択）
{json.dumps(COLLABORATION_TYPES, ensure_ascii=False, indent=2)}

以下のJSON形式で回答してください（日本語で）：
{{
  "スコア": 合計点数（整数）,
  "内訳": {{
    "エンドクライアント一致度": 点数,
    "バリューチェーン接続性": 点数,
    "市場ソリューションフィット": 点数,
    "事業拡張ポテンシャル": 点数
  }},
  "協業タイプ": "最も該当するタイプ1つ（例: A バリューチェーン型）",
  "マッチング理由": "なぜこの2人が組むべきか、具体的に150字以内で説明"
}}
"""
    try:
        res = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        text = res.content[0].text.strip()
        # JSONブロックを抽出
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        data["メンバーA名"] = a["名前"]
        data["メンバーB名"] = b["名前"]
        data["メンバーA"] = a
        data["メンバーB"] = b
        return data
    except Exception as e:
        print(f"    スコアリングエラー ({a['名前']} × {b['名前']}): {e}")
        return None


def _generate_intro(match: dict) -> str:
    """LINEグループ / Facebookグループに送る紹介文を生成"""
    a = match["メンバーA"]
    b = match["メンバーB"]
    prompt = f"""
あなたはBlendy Inc.のコーディネーターです。
以下の2人をLINE/Facebookのグループで紹介する文章を作成してください。

## 紹介するお二人
### {a['名前']}さん
- 会社名: {a['会社名']}
- 主力サービス: {a['主力サービス']}
- 強み: {a['強み']}
- 今の課題: {a['課題・足りないもの']}
- LINE: {a['LINE ID']}　Facebook: {a['Facebook URL']}

### {b['名前']}さん
- 会社名: {b['会社名']}
- 主力サービス: {b['主力サービス']}
- 強み: {b['強み']}
- 今の課題: {b['課題・足りないもの']}
- LINE: {b['LINE ID']}　Facebook: {b['Facebook URL']}

## マッチング理由
{match['マッチング理由']}

## 紹介文のルール
- 冒頭は「{a['名前']}さん・{b['名前']}さん、はじめまして！」で始める
- 差出人は「Blendy Inc.の○○」（○○はそのまま残す）
- Aさんの紹介（Bさんに向けて）→ Bさんの紹介（Aさんに向けて）→ なぜ組むべきかの理由 → 「まずはお互い簡単に自己紹介していただけますか？」で締める
- 温かく親しみやすいトーン
- 全体で300〜400字程度
- グループに両者がいる前提なので、お互いの連絡先は記載不要
"""
    try:
        res = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text.strip()
    except Exception as e:
        print(f"    紹介文生成エラー: {e}")
        return "（紹介文の生成に失敗しました）"


def _select_balanced_pairs(scored: list[dict], max_count: int) -> list[dict]:
    """
    1人が同じ回で多くマッチングされすぎないよう調整しながら上位ペアを選定
    同一人物は最大2回まで
    """
    selected = []
    name_count: dict[str, int] = {}
    for match in scored:
        if len(selected) >= max_count:
            break
        a_name = match["メンバーA名"]
        b_name = match["メンバーB名"]
        if name_count.get(a_name, 0) < 2 and name_count.get(b_name, 0) < 2:
            selected.append(match)
            name_count[a_name] = name_count.get(a_name, 0) + 1
            name_count[b_name] = name_count.get(b_name, 0) + 1
    return selected
