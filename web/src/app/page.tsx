import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function Landing() {
  return (
    <div className="center-screen">
      <div style={{ maxWidth: 380, textAlign: "center" }}>
        <div
          style={{
            fontSize: "2.4rem",
            fontWeight: 800,
            letterSpacing: "0.04em",
            marginBottom: 8,
          }}
        >
          Blendy
        </div>
        <p className="muted" style={{ fontSize: "1.02rem", lineHeight: 1.7, marginBottom: 28 }}>
          本当に組める協業パートナーを見つける。
          <br />
          業務の補完性に加え、施策スタイルと価値観の相性まで見て、
          確度の高い企業をご提案します。
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <Link href="/signup">
            <Button full>無料で会社を登録する</Button>
          </Link>
          <Link href="/login">
            <Button full variant="ghost">
              ログイン
            </Button>
          </Link>
          <Link href="/discover" style={{ marginTop: 6 }}>
            <span className="faint" style={{ fontSize: "0.85rem" }}>
              デモを見る（企業をさがす画面）→
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
