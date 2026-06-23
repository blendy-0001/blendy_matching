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

  const rot = dx / 24;
  const translateX = leaving === "like" ? 600 : leaving === "pass" ? -600 : dx;
  const interestedOpacity = Math.min(Math.max(dx / THRESHOLD, 0), 1);
  const skipOpacity = Math.min(Math.max(-dx / THRESHOLD, 0), 1);

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
        padding: 22,
        boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
        transform: `translateX(${translateX}px) rotate(${rot}deg)`,
        transition: leaving || start.current == null ? "transform .18s ease" : "none",
        touchAction: "none",
        cursor: isTop ? "grab" : "default",
        userSelect: "none",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* ヘッダ: 会社名 + 相性スコア */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ fontSize: "1.35rem", margin: 0 }}>{company.name}</h2>
          <div className="faint" style={{ fontSize: "0.8rem", marginTop: 3 }}>
            {company.industry}
          </div>
        </div>
        <span
          style={{
            flexShrink: 0,
            fontSize: "0.72rem",
            color: "var(--accent)",
            border: "1px solid var(--accent)",
            borderRadius: 6,
            padding: "4px 10px",
          }}
        >
          相性 {score}
        </span>
      </div>

      {/* 会社の基礎情報（B2B向けに前面化） */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginTop: 12,
          flexWrap: "wrap",
        }}
      >
        {company.employeeCount != null && <Chip>従業員 {company.employeeCount}名</Chip>}
        {company.revenueScale && <Chip>売上 {company.revenueScale}</Chip>}
      </div>

      <p className="muted" style={{ fontSize: "0.9rem", lineHeight: 1.65, marginTop: 12 }}>
        {profile.summary}
      </p>

      <div style={{ marginTop: "auto", display: "grid", gap: 11, paddingTop: 12 }}>
        <Mini label="提供価値" value={profile.valueProp} />
        <Mini label="強み" value={profile.strengths} />
        <Mini label="課題・求めるもの" value={profile.challenges} />
      </div>

      {/* 興味あり / 見送る のラベル */}
      <Badge text="興味あり" color="var(--interested)" opacity={interestedOpacity} side="left" />
      <Badge text="見送る" color="var(--skip)" opacity={skipOpacity} side="right" />
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        fontSize: "0.74rem",
        color: "var(--text-muted)",
        background: "var(--surface-raised)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        padding: "4px 9px",
      }}
    >
      {children}
    </span>
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
        padding: "5px 12px",
        fontWeight: 800,
        fontSize: "1rem",
        transform: `rotate(${side === "left" ? -6 : 6}deg)`,
        opacity,
        pointerEvents: "none",
      }}
    >
      {text}
    </div>
  );
}
