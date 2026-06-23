import { ReactNode } from "react";
import { TopNav } from "./TopNav";
import { BottomNav } from "./BottomNav";

/**
 * アプリ共通フレーム。
 * デスクトップ=上部ナビ、モバイル=下部ナビ（CSS のメディアクエリで切替）。
 */
export function AppFrame({ children }: { children: ReactNode }) {
  return (
    <>
      <TopNav />
      <div className="app-shell">{children}</div>
      <BottomNav />
    </>
  );
}
