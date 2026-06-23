import { AppFrame } from "@/components/AppFrame";
import { Card } from "@/components/ui/Card";
import { MOCK_COMPANIES } from "@/data/mockCompanies";

// デモ: 先頭2社を「つながり済み」として表示
const matched = MOCK_COMPANIES.slice(0, 2);

export default function MatchesPage() {
  return (
    <AppFrame>
      <h1 style={{ fontSize: "1.35rem" }}>つながり</h1>
      <p className="muted" style={{ fontSize: "0.88rem", marginBottom: 14 }}>
        相互に興味を示した企業です。ここから連絡・商談に進めます。
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
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
              商談へ →
            </span>
          </Card>
        ))}
      </div>
    </AppFrame>
  );
}
