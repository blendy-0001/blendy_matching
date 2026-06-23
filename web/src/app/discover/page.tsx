import { SwipeDeck } from "@/components/SwipeDeck";
import { AppFrame } from "@/components/AppFrame";
import { Card } from "@/components/ui/Card";
import { buildDeck } from "@/lib/deck";

export default function DiscoverPage() {
  const deck = buildDeck();
  return (
    <AppFrame>
      <div className="page-title">
        <h1 style={{ fontSize: "1.35rem" }}>企業をさがす</h1>
        <span className="faint" style={{ fontSize: "0.78rem" }}>
          相性の良い順に表示
        </span>
      </div>

      <div className="discover-layout">
        <div className="deck-col">
          <SwipeDeck initial={deck} />
        </div>

        {/* デスクトップのみ表示される情報パネル */}
        <aside className="discover-aside">
          <Card>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>表示順について</div>
            <p className="muted" style={{ fontSize: "0.86rem", lineHeight: 1.6 }}>
              業務の補完性に加え、施策スタイルや意思決定・価値観の相性をスコア化し、
              協業が成立しやすい順に並べています。
            </p>
            <div style={{ height: 12 }} />
            <div className="faint" style={{ fontSize: "0.78rem", lineHeight: 1.7 }}>
              操作: カードを左右にドラッグ、または下のボタンで
              <br />「興味あり / 見送る」を選択できます。
            </div>
          </Card>
        </aside>
      </div>
    </AppFrame>
  );
}
