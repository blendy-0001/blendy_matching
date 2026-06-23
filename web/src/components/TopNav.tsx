"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "./nav";

/** デスクトップ（Web版）用の上部ナビ。CSS で 860px 以上のみ表示。 */
export function TopNav() {
  const path = usePathname();
  return (
    <header className="top-nav">
      <Link href="/discover" className="brand">
        Blendy
      </Link>
      <nav className="links">
        {NAV_ITEMS.map(({ href, label, Icon }) => (
          <Link key={href} href={href} className={path.startsWith(href) ? "active" : ""}>
            <Icon className="nav-icon" />
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
