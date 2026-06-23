"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "./nav";

export function BottomNav() {
  const path = usePathname();
  return (
    <nav className="bottom-nav">
      {NAV_ITEMS.map(({ href, short, Icon }) => (
        <Link key={href} href={href} className={path.startsWith(href) ? "active" : ""}>
          <Icon />
          {short}
        </Link>
      ))}
    </nav>
  );
}
