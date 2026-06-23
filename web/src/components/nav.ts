import { IconSearch, IconConnections, IconBuilding } from "./Icons";

/** ナビ項目（トップ/ボトム共通）。B2B寄りのラベル。 */
export const NAV_ITEMS = [
  { href: "/discover", label: "企業をさがす", short: "さがす", Icon: IconSearch },
  { href: "/matches", label: "つながり", short: "つながり", Icon: IconConnections },
  { href: "/profile", label: "自社プロフィール", short: "自社", Icon: IconBuilding },
] as const;
