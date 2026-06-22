"use client";

import { useState } from "react";
import { DeckCandidate, SwipeDirection } from "@/lib/types";
import { SwipeCard } from "./SwipeCard";

export function SwipeDeck({ initial }: { initial: DeckCandidate[] }) {
  const [index, setIndex] = useState(0);
  const [liked, setLiked] = useState<string[]>([]);

  const remaining = initial.slice(index);
  const current = remaining[0];

  function resolve(dir: SwipeDirection) {
    if (current && dir === "like") setLiked((l) => [...l, current.company.name]);
    setIndex((i) => i + 1);
  }

  if (!current) {
    return (
      <div style={{ textAlign: "center", padding: "60px 12px" }}>
        <div style={{ fontSize: "2rem", marginBottom: 8 }}>🎉</div>
        <h2>今日の候補は以上です</h2>
        <p className="muted" style={{ fontSize: "0.9rem" }}>
          {liked.length > 0
            ? `${liked.length}社にLikeしました。相互Likeでマッチが成立します。`
            : "また新しい候補が入ったらお知らせします。"}
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* カードスタック */}
      <div style={{ position: "relative", height: 460, marginTop: 6 }}>
        {remaining
          .slice(0, 2)
          .reverse()
          .map((c, i, arr) => {
            const isTop = i === arr.length - 1;
            return (
              <div
                key={c.company.id}
                style={{
                  position: "absolute",
                  inset: 0,
                  transform: isTop ? "none" : "scale(0.96) translateY(10px)",
                  transition: "transform .2s ease",
                }}
              >
                <SwipeCard candidate={c} onResolved={resolve} isTop={isTop} />
              </div>
            );
          })}
      </div>

      {/* アクションボタン */}
      <div style={{ display: "flex", justifyContent: "center", gap: 22, marginTop: 22 }}>
        <RoundBtn label="パス" color="var(--pass)" onClick={() => resolve("pass")}>
          ✕
        </RoundBtn>
        <RoundBtn label="いいね" color="var(--like)" onClick={() => resolve("like")}>
          ♥
        </RoundBtn>
      </div>
    </div>
  );
}

function RoundBtn({
  children,
  color,
  label,
  onClick,
}: {
  children: React.ReactNode;
  color: string;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      style={{
        width: 64,
        height: 64,
        borderRadius: "50%",
        background: "var(--surface-raised)",
        border: `2px solid ${color}`,
        color,
        fontSize: "1.5rem",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {children}
    </button>
  );
}
