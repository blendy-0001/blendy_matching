"use client";

import { useState } from "react";
import { DeckCandidate, SwipeDirection } from "@/lib/types";
import { SwipeCard } from "./SwipeCard";
import { IconCheck, IconClose } from "./Icons";

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
        <h2>本日の候補は以上です</h2>
        <p className="muted" style={{ fontSize: "0.9rem" }}>
          {liked.length > 0
            ? `${liked.length}社に「興味あり」を送りました。相手も興味を示すと、つながり（商談可能）になります。`
            : "新しい候補が入り次第お知らせします。"}
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
      <div style={{ display: "flex", justifyContent: "center", gap: 14, marginTop: 22 }}>
        <ActionBtn label="見送る" color="var(--skip)" onClick={() => resolve("pass")} Icon={IconClose} />
        <ActionBtn
          label="興味あり"
          color="var(--interested)"
          onClick={() => resolve("like")}
          Icon={IconCheck}
          primary
        />
      </div>
    </div>
  );
}

function ActionBtn({
  label,
  color,
  onClick,
  Icon,
  primary,
}: {
  label: string;
  color: string;
  onClick: () => void;
  Icon: (p: { className?: string }) => React.ReactElement;
  primary?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        maxWidth: 200,
        height: 50,
        borderRadius: "var(--radius)",
        background: primary ? color : "var(--surface-raised)",
        border: `1px solid ${primary ? color : "var(--border)"}`,
        color: primary ? "var(--on-accent)" : "var(--text)",
        fontSize: "0.95rem",
        fontWeight: 700,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
      }}
    >
      <Icon className="nav-icon" />
      {label}
    </button>
  );
}
