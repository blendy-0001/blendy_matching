/**
 * カラートークン（切り出し）
 * ───────────────────────────────────────────────
 * ここがテーマの「単一の真実」。色を変えたいときはこのファイルと
 * 対になる tokens.css の値を差し替えるだけでよい。
 *
 * 3層構成:
 *   primitive … 生の色値（パレット）
 *   semantic  … 役割（背景・文字・アクセント等）。UI はこちらだけを参照する
 *
 * 現在のテーマ: ダーク / ブラック基調・アクセント1色（後で差し替え可能）
 */

// ── primitive（パレット） ──────────────────────────
export const primitive = {
  black: "#0a0a0b",
  ink900: "#101012",
  ink800: "#161619",
  ink700: "#1e1e22",
  ink600: "#26262b",
  ink500: "#34343b",
  gray400: "#6b6b76",
  gray300: "#9a9aa6",
  gray200: "#c7c7d1",
  white: "#f5f5f7",
  // アクセント（ここを変えるとブランドカラーが変わる）
  accent: "#6e56cf",
  accentHover: "#7c66d9",
  // ステータス
  success: "#3fb37f",
  danger: "#e5484d",
  like: "#3fb37f",
  pass: "#e5484d",
} as const;

// ── semantic（役割） ──────────────────────────────
export const semantic = {
  bg: primitive.black, // 画面の最背面
  surface: primitive.ink800, // カード・パネル
  surfaceRaised: primitive.ink700, // 浮いた要素
  border: primitive.ink600,
  text: primitive.white, // 主要テキスト
  textMuted: primitive.gray300, // 補助テキスト
  textFaint: primitive.gray400, // さらに薄い
  accent: primitive.accent,
  accentHover: primitive.accentHover,
  onAccent: primitive.white,
  success: primitive.success,
  danger: primitive.danger,
  like: primitive.like,
  pass: primitive.pass,
} as const;

export type SemanticColor = keyof typeof semantic;
