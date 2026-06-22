import { SwipeDeck } from "@/components/SwipeDeck";
import { BottomNav } from "@/components/BottomNav";
import { buildDeck } from "@/lib/deck";

export default function DiscoverPage() {
  const deck = buildDeck();
  return (
    <div className="app-shell">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1 style={{ fontSize: "1.35rem" }}>さがす</h1>
        <span className="faint" style={{ fontSize: "0.78rem" }}>
          相性の良い順
        </span>
      </div>
      <SwipeDeck initial={deck} />
      <BottomNav />
    </div>
  );
}
