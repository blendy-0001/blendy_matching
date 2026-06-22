import { NextRequest, NextResponse } from "next/server";
import { getClaude, CLAUDE_MODEL, parseJsonLoose } from "@/lib/claude";
import {
  PROFILE_GEN_SYSTEM,
  buildProfileGenUser,
  ProfileDraft,
  ProfileGenInput,
} from "@/lib/prompts/companyProfile";

/**
 * HP本文・紹介資料テキストから企業プロフィールの叩きを生成。
 * ANTHROPIC_API_KEY があれば Claude、無ければデモ用モックを返す。
 *
 * NOTE: HP の取得（URL→本文抽出）と PDF パースは E3 で追加実装予定。
 *       現状は呼び出し側から websiteText / documentText を受け取る。
 */
export async function POST(req: NextRequest) {
  const input = (await req.json()) as ProfileGenInput;

  const claude = getClaude();
  if (!claude) {
    return NextResponse.json({ ...mockDraft(input), _mock: true });
  }

  try {
    const msg = await claude.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: 1200,
      system: PROFILE_GEN_SYSTEM,
      messages: [{ role: "user", content: buildProfileGenUser(input) }],
    });
    const text = msg.content.find((c) => c.type === "text")?.text ?? "{}";
    return NextResponse.json(parseJsonLoose<ProfileDraft>(text));
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "generate failed" },
      { status: 500 },
    );
  }
}

function mockDraft(input: ProfileGenInput): ProfileDraft {
  return {
    summary: `${input.companyName}（${input.industry}）の会社サマリの叩きです。HP・紹介資料を読み込むと、ここに事実ベースの概要が入ります。`,
    valueProp: "（要記入）提供している価値を1-2文で。",
    strengths: "（要記入）強みを記載。",
    challenges: "（要記入）課題・協業で補いたいことを記載。",
    targetMarket: "（要記入）対象市場・顧客像を記載。",
  };
}
