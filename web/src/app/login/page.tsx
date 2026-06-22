"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Field, TextInput } from "@/components/ui/Field";
import { getBrowserSupabase } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    const fd = new FormData(e.currentTarget);
    const supabase = getBrowserSupabase();
    if (!supabase) {
      router.push("/discover"); // デモ: 認証なしでスワイプ画面へ
      return;
    }
    const { error } = await supabase.auth.signInWithPassword({
      email: String(fd.get("email")),
      password: String(fd.get("password")),
    });
    setBusy(false);
    if (error) setMsg(`エラー: ${error.message}`);
    else router.push("/discover");
  }

  return (
    <div className="app-shell">
      <h1 style={{ fontSize: "1.5rem", marginTop: 24 }}>ログイン</h1>
      <form onSubmit={onSubmit}>
        <Field label="メールアドレス" required>
          <TextInput name="email" type="email" required />
        </Field>
        <Field label="パスワード" required>
          <TextInput name="password" type="password" required />
        </Field>
        <div style={{ height: 18 }} />
        <Button full type="submit" disabled={busy}>
          {busy ? "確認中…" : "ログイン"}
        </Button>
      </form>
      {msg && (
        <p className="muted" style={{ marginTop: 14, fontSize: "0.88rem" }}>
          {msg}
        </p>
      )}
      <p className="faint" style={{ marginTop: 18, fontSize: "0.85rem", textAlign: "center" }}>
        アカウントが無いですか？ <Link href="/signup" style={{ color: "var(--accent)" }}>新規登録</Link>
      </p>
    </div>
  );
}
