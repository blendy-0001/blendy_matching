import { BottomNav } from "@/components/BottomNav";
import { Card } from "@/components/ui/Card";
import { MOCK_COMPANIES } from "@/data/mockCompanies";

// デモ: 先頭2社を「マッチ済み」として表示
const matched = MOCK_COMPANIES.slice(0, 2);

export default function MatchesPage() {
  return (
    <div className="app-shell">
      <h1 style={{ fontSize: "1.35rem" }}>マッチ</h1>
      <p className="muted" style={{ fontSize: "0.88rem", marginBottom: 14 }}>
        相互にLikeした企業。ここから連絡・商談へ。
      </p>

      <div style={{ display: "grid", gap: 12 }}>
        {matched.map(({ company, profile }) => (
          <Card key={company.id} style={{ display: "flex", gap: 14, alignItems: "center" }}>
            <div
              style={{
                width: 46,
                height: 46,
                borderRadius: 12,
                background: "var(--surface-raised)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
              }}
            >
              {company.name.slice(0, 1)}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700 }}>{company.name}</div>
              <div
                className="faint"
                style={{
                  fontSize: "0.82rem",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {profile.valueProp}
              </div>
            </div>
            <span className="faint" style={{ fontSize: "0.78rem" }}>
              商談 →
            </span>
          </Card>
        ))}
      </div>

      <BottomNav />
    </div>
  );
}
