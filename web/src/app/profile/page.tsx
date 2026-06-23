"use client";

import { useState } from "react";
import Link from "next/link";
import { AppFrame } from "@/components/AppFrame";
import { Button } from "@/components/ui/Button";
import { Field, TextInput, Textarea } from "@/components/ui/Field";

// デモ用の初期プロフィール（本番は自社の company_profiles を読む）
const INITIAL = {
  summary:
    "中小企業向けの業務自動化SaaSを開発・提供。導入から定着支援までを一気通貫で行う。",
  valueProp: "バックオフィス業務の自動化で、現場の工数を平均30%削減。",
  strengths: "プロダクト開発力、クラウドネイティブな実装、定着支援。",
  challenges: "新規顧客の獲得チャネルが限られ、営業リソースが不足。",
  targetMarket: "従業員50〜300名のサービス業・製造業。",
};

export default function ProfilePage() {
  const [p, setP] = useState(INITIAL);
  const [saved, setSaved] = useState(false);
  const set = (k: keyof typeof INITIAL) => (e: { target: { value: string } }) => {
    setP({ ...p, [k]: e.target.value });
    setSaved(false);
  };

  return (
    <AppFrame>
      <div className="content-narrow">
      <h1 style={{ fontSize: "1.35rem" }}>会社プロフィール</h1>
      <p className="muted" style={{ fontSize: "0.86rem", marginBottom: 6 }}>
        AIが下書きした内容です。自由に編集して整えてください。
      </p>
      <Link href="/profile/generate" className="faint" style={{ fontSize: "0.82rem", color: "var(--accent)" }}>
        HP・紹介資料からAIで作り直す →
      </Link>

      <div style={{ marginTop: 10 }}>
        <Field label="会社サマリ">
          <Textarea value={p.summary} onChange={set("summary")} />
        </Field>
        <Field label="提供価値">
          <TextInput value={p.valueProp} onChange={set("valueProp")} />
        </Field>
        <Field label="強み">
          <TextInput value={p.strengths} onChange={set("strengths")} />
        </Field>
        <Field label="課題・求めるもの">
          <TextInput value={p.challenges} onChange={set("challenges")} />
        </Field>
        <Field label="対象市場・顧客像">
          <TextInput value={p.targetMarket} onChange={set("targetMarket")} />
        </Field>

        <div style={{ height: 16 }} />
        <Button full onClick={() => setSaved(true)}>
          保存する
        </Button>
        {saved && (
          <p className="muted" style={{ marginTop: 10, fontSize: "0.85rem" }}>
            （デモ）保存しました。DB接続後に永続化されます。
          </p>
        )}

        <div style={{ height: 18 }} />
        <Link href="/meetings">
          <Button full variant="ghost">
            商談議事録から情報を更新する →
          </Button>
        </Link>
      </div>
      </div>
    </AppFrame>
  );
}
