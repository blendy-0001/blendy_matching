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
          本当に組める協業パートナーと出会う。
          <br />
          業務の補完性だけでなく、施策スタイルと価値観まで見て。
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <Link href="/signup">
            <Button full>はじめる</Button>
          </Link>
          <Link href="/login">
            <Button full variant="ghost">
              ログイン
            </Button>
          </Link>
          <Link href="/discover" style={{ marginTop: 6 }}>
            <span className="faint" style={{ fontSize: "0.85rem" }}>
              デモを見る（スワイプ画面）→
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
