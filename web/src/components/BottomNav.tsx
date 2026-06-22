"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/discover", label: "さがす", icon: "🔥" },
  { href: "/matches", label: "マッチ", icon: "💬" },
  { href: "/profile", label: "プロフィール", icon: "🏢" },
];

export function BottomNav() {
  const path = usePathname();
  return (
    <nav className="bottom-nav">
      {items.map((it) => (
        <Link
          key={it.href}
          href={it.href}
          className={path.startsWith(it.href) ? "active" : ""}
        >
          <span style={{ fontSize: "1.2rem" }}>{it.icon}</span>
          {it.label}
        </Link>
      ))}
    </nav>
  );
}
