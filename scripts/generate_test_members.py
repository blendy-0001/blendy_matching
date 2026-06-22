"""
50人のテストメンバーをNotionに一括追加
"""
import sys
import io
import notion_client

# UTF-8 エンコーディング対応
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# テストメンバーのテンプレート
INDUSTRIES = [
    "IT・SaaS", "教育", "HR", "金融", "デザイン", "マーケティング",
    "サプライチェーン", "法務", "クリエイティブ", "営業支援"
]

VALUE_CHAINS = [
    "認知・ブランディング",
    "集客・マーケティング",
    "リード獲得・見込み客育成",
    "営業・提案・クロージング",
    "制作・開発・導入",
    "運用・保守・継続支援",
    "教育・研修・人材育成",
    "経営・戦略・資金調達",
]

STRENGTHS = [
    "営業能力", "開発技術", "マーケティング", "ネットワーク",
    "顧客管理", "実装力", "ノウハウ", "企画力", "デザイン", "人脈"
]

ISSUES = [
    "営業チャネルが不足", "技術実装が必要", "マーケティングが必要",
    "顧客が不足", "開発人材が不足", "資金調達", "ネットワーク拡大"
]

BUSINESS_PHASES = ["成長期", "安定期", "拡大期"]

def generate_member(num):
    """テストメンバーを生成"""
    name = f"テスト{num:02d}"
    company = f"{INDUSTRIES[num % len(INDUSTRIES)]} {num:02d}"

    return {
        "名前": name,
        "会社名": company,
        "主力サービス": f"サービス{num}",
        "エンドクライアント業界": INDUSTRIES[num % len(INDUSTRIES)],
        "エンドクライアント規模": ["スタートアップ", "中堅企業", "大企業"][num % 3],
        "クライアントの課題": ISSUES[num % len(ISSUES)],
        "バリューチェーン位置": [
            VALUE_CHAINS[num % len(VALUE_CHAINS)],
            VALUE_CHAINS[(num + 1) % len(VALUE_CHAINS)]
        ],
        "強み": " + ".join([STRENGTHS[num % len(STRENGTHS)], STRENGTHS[(num + 1) % len(STRENGTHS)]]),
        "課題・足りないもの": ISSUES[num % len(ISSUES)],
        "業種カテゴリ": INDUSTRIES[num % len(INDUSTRIES)],
        "事業フェーズ": BUSINESS_PHASES[num % len(BUSINESS_PHASES)],
        "LINE ID": f"line-test{num:02d}",
        "Facebook URL": f"facebook.com/test{num:02d}",
    }

def add_members():
    """50人のメンバーをNotionに追加"""
    print("[STEP 1] テストメンバーを生成中...\n")

    added = 0
    failed = 0

    for i in range(1, 51):
        try:
            member_data = generate_member(i)
            page_id = notion_client.create_member(member_data)
            if page_id:
                added += 1
                print(f"  [OK] テスト{i:02d} を追加")
                if i % 10 == 0:
                    print(f"  → 計 {i}人追加完了\n")
            else:
                failed += 1
                print(f"  [ERROR] テスト{i:02d} 追加失敗: ページID未取得")
        except Exception as e:
            print(f"  [ERROR] テスト{i:02d} 追加失敗: {e}")
            failed += 1

    print(f"\n[DONE] {added}人のテストメンバーをNotionに追加しました")
    if failed > 0:
        print(f"[WARN] {failed}人の追加に失敗しました")

    return added

if __name__ == "__main__":
    add_members()
