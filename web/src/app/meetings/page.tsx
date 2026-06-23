"use client";

import { useState } from "react";
import { AppFrame } from "@/components/AppFrame";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Textarea } from "@/components/ui/Field";
import type { FieldChange, MeetingUpdateResult } from "@/lib/prompts/meetingUpdate";

const CURRENT_PROFILE = {
  summary: "中小企業向けの業務自動化SaaSを開発・提供。",
  valueProp: "バックオフィス業務の自動化で工数を平均30%削減。",
  strengths: "プロダクト開発力、定着支援。",
  challenges: "新規顧客の獲得チャネルが限られ、営業リソースが不足。",
  targetMarket: "従業員50〜300名のサービス業・製造業。",
};

export default function MeetingsPage() {
  const [minutes, setMinutes] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<MeetingUpdateResult | null>(null);
  const [accepted, setAccepted] = useState<Record<number, boolean>>({});
  const [applied, setApplied] = useState(false);

  async function analyze() {
    setBusy(true);
    setResult(null);
    setApplied(false);
    const res = await fetch("/api/meetings/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        companyName: "自社",
        currentProfile: CURRENT_PROFILE,
        currentSalesNotes: "",
        minutesText: minutes,
      }),
    });
    const data = (await res.json()) as MeetingUpdateResult;
    setResult(data);
    // 高 confidence かつ要確認でないものを既定で承認チェック
    const init: Record<number, boolean> = {};
    (data.profileChanges || []).forEach((c, i) => {
      init[i] = c.confidence >= 0.7 && !c.needsReview;
    });
    setAccepted(init);
    setBusy(false);
  }

  return (
    <AppFrame>
      <div className="content-narrow">
      <h1 style={{ fontSize: "1.35rem" }}>商談議事録から更新</h1>
      <p className="muted" style={{ fontSize: "0.86rem", marginBottom: 10 }}>
        議事録を貼り付けると、AIが企業情報・営業情報の<strong>更新案</strong>を提案します。
        承認したものだけが反映されます。
      </p>

      <Field label="議事録">
        <Textarea
          value={minutes}
          onChange={(e) => setMinutes(e.target.value)}
          placeholder="商談の議事録を貼り付け…"
          style={{ minHeight: 150 }}
        />
      </Field>
      <div style={{ height: 12 }} />
      <Button full onClick={analyze} disabled={busy || minutes.trim().length < 10}>
        {busy ? "分析中…" : "AIで更新案を作成"}
      </Button>

      {result && (
        <div style={{ marginTop: 22 }}>
          <h2 style={{ fontSize: "1.05rem" }}>更新案（承認するものを選択）</h2>

          {(result.profileChanges || []).length === 0 && (
            <p className="muted" style={{ fontSize: "0.88rem" }}>
              プロフィールの更新提案はありませんでした。
            </p>
          )}

          <div style={{ display: "grid", gap: 12, marginTop: 8 }}>
            {(result.profileChanges || []).map((c, i) => (
              <ChangeCard
                key={i}
                change={c}
                checked={!!accepted[i]}
                onToggle={() => setAccepted({ ...accepted, [i]: !accepted[i] })}
              />
            ))}
          </div>

          {result.salesInfo && (
            <Card style={{ marginTop: 14 }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>営業情報（抽出）</div>
              {Object.entries(result.salesInfo)
                .filter(([, v]) => v)
                .map(([k, v]) => (
                  <div key={k} style={{ display: "flex", gap: 10, fontSize: "0.88rem", marginBottom: 4 }}>
                    <span className="faint" style={{ minWidth: 76 }}>
                      {salesLabel(k)}
                    </span>
                    <span>{v as string}</span>
                  </div>
                ))}
            </Card>
          )}

          <div style={{ height: 16 }} />
          <Button full onClick={() => setApplied(true)}>
            選択した更新を反映する
          </Button>
          {applied && (
            <p className="muted" style={{ marginTop: 10, fontSize: "0.85rem" }}>
              （デモ）承認した {Object.values(accepted).filter(Boolean).length} 件を反映しました。
              DB接続後に永続化されます。
            </p>
          )}
        </div>
      )}
      </div>
    </AppFrame>
  );
}

function ChangeCard({
  change,
  checked,
  onToggle,
}: {
  change: FieldChange;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <Card style={{ borderColor: checked ? "var(--accent)" : "var(--border)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>{fieldLabel(change.field)}</span>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.82rem" }}>
          <input type="checkbox" checked={checked} onChange={onToggle} />
          反映する
        </label>
      </div>

      <div style={{ marginTop: 8, fontSize: "0.86rem", lineHeight: 1.5 }}>
        <div className="faint" style={{ textDecoration: "line-through" }}>
          {change.before || "（空）"}
        </div>
        <div style={{ color: "var(--success)" }}>{change.after}</div>
      </div>

      <div className="faint" style={{ marginTop: 8, fontSize: "0.76rem" }}>
        根拠: 「{change.evidence}」 / 確度 {Math.round(change.confidence * 100)}%
        {change.needsReview && (
          <span style={{ color: "var(--danger)" }}> ・要確認（既存と矛盾の可能性）</span>
        )}
      </div>
    </Card>
  );
}

const fieldLabels: Record<string, string> = {
  summary: "会社サマリ",
  valueProp: "提供価値",
  strengths: "強み",
  challenges: "課題・求めるもの",
  targetMarket: "対象市場",
};
const fieldLabel = (f: string) => fieldLabels[f] ?? f;

const salesLabels: Record<string, string> = {
  challenge: "課題",
  budget: "予算感",
  decisionMaker: "決裁者",
  timeline: "時間軸",
  nextAction: "次アクション",
};
const salesLabel = (k: string) => salesLabels[k] ?? k;
