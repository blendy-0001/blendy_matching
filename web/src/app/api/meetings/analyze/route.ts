import { NextRequest, NextResponse } from "next/server";
import { getClaude, CLAUDE_MODEL, parseJsonLoose } from "@/lib/claude";
import {
  MEETING_UPDATE_SYSTEM,
  buildMeetingUpdateUser,
  MeetingUpdateInput,
  MeetingUpdateResult,
  PROMPT_VERSION,
} from "@/lib/prompts/meetingUpdate";

/**
 * 議事録 → 更新差分の提案（提案→承認型）。
 * ANTHROPIC_API_KEY があれば Claude、無ければデモ用のモック差分を返す。
 */
export async function POST(req: NextRequest) {
  const input = (await req.json()) as MeetingUpdateInput;

  const claude = getClaude();
  if (!claude) {
    return NextResponse.json({ ...mockResult(input), _mock: true, promptVersion: PROMPT_VERSION });
  }

  try {
    const msg = await claude.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: 1500,
      system: MEETING_UPDATE_SYSTEM,
      messages: [{ role: "user", content: buildMeetingUpdateUser(input) }],
    });
    const text = msg.content.find((c) => c.type === "text")?.text ?? "{}";
    const parsed = parseJsonLoose<MeetingUpdateResult>(text);
    return NextResponse.json({ ...parsed, promptVersion: PROMPT_VERSION });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "analyze failed" },
      { status: 500 },
    );
  }
}

function mockResult(input: MeetingUpdateInput): MeetingUpdateResult {
  return {
    profileChanges: [
      {
        field: "challenges",
        before: input.currentProfile.challenges,
        after: "新規顧客の獲得チャネル拡大に加え、医療業界への参入支援を求めている。",
        evidence: "「医療系の販路を持つパートナーと組みたい」との発言",
        confidence: 0.8,
        needsReview: false,
      },
    ],
    salesInfo: {
      challenge: "医療業界の販路がなく単独での参入が難しい",
      budget: "年間500万円程度を想定",
      decisionMaker: "代表取締役",
      timeline: "次四半期から検討開始",
      nextAction: "提案資料を作成し再商談を設定",
    },
    notes: "（デモ）ANTHROPIC_API_KEY 設定後は議事録から実際の差分を生成します。",
  };
}
