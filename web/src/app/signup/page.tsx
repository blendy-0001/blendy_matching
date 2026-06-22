"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Field, TextInput, Select } from "@/components/ui/Field";
import { getBrowserSupabase } from "@/lib/supabase/client";

const INDUSTRIES = [
  "IT",
  "金融",
  "製造",
  "建設",
  "不動産",
  "流通",
  "サービス",
  "医療",
  "教育",
  "メディア",
  "その他",
];

const REVENUE = ["1億未満", "1〜5億", "5〜10億", "10億以上"];

export default function SignupPage() {
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    const fd = new FormData(e.currentTarget);
    const payload = {
      fullName: fd.get("fullName"),
      roleTitle: fd.get("roleTitle"),
      companyName: fd.get("companyName"),
      email: fd.get("email"),
      password: fd.get("password"),
      officerCount: fd.get("officerCount"),
      industry: fd.get("industry"),
      revenueScale: fd.get("revenueScale"),
      employeeCount: fd.get("employeeCount"),
    };

    const supabase = getBrowserSupabase();
    if (!supabase) {
      // DB 未接続時はデモとして次のステップへ進める
      setMsg(
        "（デモ環境）登録内容を受け付けました。Supabase 接続後に本番登録が有効になります。",
      );
      setBusy(false);
      return;
    }

    const { error } = await supabase.auth.signUp({
      email: String(payload.email),
      password: String(payload.password),
      options: { data: { full_name: payload.fullName } },
    });
    // NOTE: company / users への保存は E1 のサーバAction + RLS で実装予定
    setBusy(false);
    setMsg(error ? `エラー: ${error.message}` : "確認メールを送信しました。");
  }

  return (
    <div className="app-shell">
      <h1 style={{ fontSize: "1.5rem" }}>アカウント作成</h1>
      <p className="muted" style={{ fontSize: "0.9rem", marginBottom: 8 }}>
        まずは最低限の情報だけ。会社プロフィールは後でAIが下書きします。
      </p>

      <form onSubmit={onSubmit}>
        <Field label="氏名" required>
          <TextInput name="fullName" required />
        </Field>
        <Field label="役職" required>
          <TextInput name="roleTitle" placeholder="代表 / 事業責任者 など" required />
        </Field>
        <Field label="会社名" required>
          <TextInput name="companyName" required />
        </Field>
        <Field label="メールアドレス（ログインID）" required>
          <TextInput name="email" type="email" required />
        </Field>
        <Field label="パスワード" required>
          <TextInput name="password" type="password" minLength={8} required />
        </Field>
        <Field label="役員数" required>
          <TextInput name="officerCount" type="number" min={0} required />
        </Field>
        <Field label="業種" required>
          <Select name="industry" required defaultValue="">
            <option value="" disabled>
              選択してください
            </option>
            {INDUSTRIES.map((i) => (
              <option key={i}>{i}</option>
            ))}
          </Select>
        </Field>
        <Field label="売上規模（任意）">
          <Select name="revenueScale" defaultValue="">
            <option value="">未選択</option>
            {REVENUE.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </Select>
        </Field>
        <Field label="従業員数" required>
          <TextInput name="employeeCount" type="number" min={1} required />
        </Field>

        <div style={{ height: 18 }} />
        <Button full type="submit" disabled={busy}>
          {busy ? "送信中…" : "登録してプロフィール作成へ"}
        </Button>
      </form>

      {msg && (
        <p className="muted" style={{ marginTop: 14, fontSize: "0.88rem" }}>
          {msg}
        </p>
      )}

      <p className="faint" style={{ marginTop: 18, fontSize: "0.85rem", textAlign: "center" }}>
        既にアカウントをお持ちですか？ <Link href="/login" style={{ color: "var(--accent)" }}>ログイン</Link>
      </p>
    </div>
  );
}
