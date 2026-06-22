"use client";

import { useRef, useState } from "react";
import { DeckCandidate, SwipeDirection } from "@/lib/types";

interface Props {
  candidate: DeckCandidate;
  onResolved: (dir: SwipeDirection) => void;
  isTop: boolean;
}

const THRESHOLD = 110;

/** ポインタドラッグで left/right スワイプできるカード（外部ライブラリ不使用）。 */
export function SwipeCard({ candidate, onResolved, isTop }: Props) {
  const [dx, setDx] = useState(0);
  const [leaving, setLeaving] = useState<null | SwipeDirection>(null);
  const start = useRef<number | null>(null);
  const { company, profile, score } = candidate;

  function down(e: React.PointerEvent) {
    if (!isTop) return;
    start.current = e.clientX;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
  function move(e: React.PointerEvent) {
    if (start.current == null) return;
    setDx(e.clientX - start.current);
  }
  function up() {
    if (start.current == null) return;
    start.current = null;
    if (dx > THRESHOLD) fly("like");
    else if (dx < -THRESHOLD) fly("pass");
    else setDx(0);
  }
  function fly(dir: SwipeDirection) {
    setLeaving(dir);
    setTimeout(() => onResolved(dir), 180);
  }

  const rot = dx / 18;
  const translateX = leaving === "like" ? 600 : leaving === "pass" ? -600 : dx;
  const likeOpacity = Math.min(Math.max(dx / THRESHOLD, 0), 1);
  const passOpacity = Math.min(Math.max(-dx / THRESHOLD, 0), 1);

  return (
    <div
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      style={{
        position: "absolute",
        inset: 0,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: 20,
        boxShadow: "0 12px 40px rgba(0,0,0,0.45)",
        transform: `translateX(${translateX}px) rotate(${rot}deg)`,
        transition: leaving || start.current == null ? "transform .18s ease" : "none",
        touchAction: "none",
        cursor: isTop ? "grab" : "default",
        userSelect: "none",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* スコアバッジ */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span
          style={{
            fontSize: "0.72rem",
            color: "var(--accent)",
            border: "1px solid var(--accent)",
            borderRadius: 999,
            padding: "3px 10px",
          }}
        >
          相性スコア {score}
        </span>
        <span className="faint" style={{ fontSize: "0.78rem" }}>
          {company.industry}・{company.employeeCount}名
        </span>
      </div>

      <h2 style={{ fontSize: "1.5rem", marginTop: 14 }}>{company.name}</h2>
      <p className="muted" style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>
        {profile.summary}
      </p>

      <div style={{ marginTop: "auto", display: "grid", gap: 10 }}>
        <Mini label="提供価値" value={profile.valueProp} />
        <Mini label="強み" value={profile.strengths} />
        <Mini label="課題・求めるもの" value={profile.challenges} />
      </div>

      {/* LIKE / PASS のラベル */}
      <Badge text="LIKE" color="var(--like)" opacity={likeOpacity} side="left" />
      <Badge text="PASS" color="var(--pass)" opacity={passOpacity} side="right" />
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="faint" style={{ fontSize: "0.72rem", marginBottom: 2 }}>
        {label}
      </div>
      <div style={{ fontSize: "0.9rem", lineHeight: 1.5 }}>{value}</div>
    </div>
  );
}

function Badge({
  text,
  color,
  opacity,
  side,
}: {
  text: string;
  color: string;
  opacity: number;
  side: "left" | "right";
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: 22,
        [side]: 22,
        color,
        border: `3px solid ${color}`,
        borderRadius: 8,
        padding: "4px 10px",
        fontWeight: 800,
        fontSize: "1.1rem",
        transform: `rotate(${side === "left" ? -14 : 14}deg)`,
        opacity,
        pointerEvents: "none",
      }}
    >
      {text}
    </div>
  );
}
