"use client";

import { useState } from "react";
import Link from "next/link";
import { AppFrame } from "@/components/AppFrame";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, TextInput, Textarea } from "@/components/ui/Field";
import type { ProfileDraft } from "@/lib/prompts/companyProfile";

export default function GenerateProfilePage() {
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState<ProfileDraft | null>(null);

  async function generate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setDraft(null);
    const fd = new FormData(e.currentTarget);
    const res = await fetch("/api/profile/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        companyName: fd.get("companyName"),
        industry: fd.get("industry"),
        websiteText: fd.get("websiteText"),
        documentText: fd.get("documentText"),
      }),
    });
    setDraft((await res.json()) as ProfileDraft);
    setBusy(false);
  }

  return (
    <AppFrame>
      <div className="content-narrow">
      <h1 style={{ fontSize: "1.35rem" }}>AIで会社プロフィール作成</h1>
      <p className="muted" style={{ fontSize: "0.86rem", marginBottom: 12 }}>
        HPと会社紹介資料を読み込んで「叩き台」を生成します。あとから編集できます。
      </p>

      <form onSubmit={generate}>
        <Field label="会社名" required>
          <TextInput name="companyName" required />
        </Field>
        <Field label="業種" required>
          <TextInput name="industry" required />
        </Field>
        <Field label="HP本文（または会社紹介の貼り付け）">
          <Textarea name="websiteText" placeholder="HPの会社紹介テキストを貼り付け…" />
        </Field>
        <Field label="会社紹介資料のテキスト（任意）">
          <Textarea name="documentText" placeholder="資料の要点を貼り付け…（PDFアップロードは今後対応）" />
        </Field>
        <div style={{ height: 14 }} />
        <Button full type="submit" disabled={busy}>
          {busy ? "生成中…" : "叩き台を生成"}
        </Button>
      </form>

      {draft && (
        <Card style={{ marginTop: 18 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>生成された叩き台</div>
          {(
            [
              ["会社サマリ", draft.summary],
              ["提供価値", draft.valueProp],
              ["強み", draft.strengths],
              ["課題・求めるもの", draft.challenges],
              ["対象市場", draft.targetMarket],
            ] as const
          ).map(([label, value]) => (
            <div key={label} style={{ marginBottom: 10 }}>
              <div className="faint" style={{ fontSize: "0.74rem" }}>
                {label}
              </div>
              <div style={{ fontSize: "0.9rem", lineHeight: 1.55 }}>{value}</div>
            </div>
          ))}
          <Link href="/profile">
            <Button full variant="ghost">
              編集して保存する →
            </Button>
          </Link>
        </Card>
      )}
      </div>
    </AppFrame>
  );
}
