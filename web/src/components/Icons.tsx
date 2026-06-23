/** 業務寄りのシンプルなラインアイコン（絵文字を使わない）。 */
type P = { className?: string };
const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function IconSearch({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </svg>
  );
}

export function IconConnections({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <circle cx="7" cy="8" r="3" />
      <circle cx="17" cy="16" r="3" />
      <path d="M9.5 9.5l5 5" />
    </svg>
  );
}

export function IconBuilding({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <rect x="5" y="3" width="14" height="18" rx="1.5" />
      <path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2" />
    </svg>
  );
}

export function IconDoc({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <path d="M7 3h7l4 4v14H7z" />
      <path d="M14 3v4h4M10 13h5M10 17h5" />
    </svg>
  );
}

export function IconCheck({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <path d="M5 12.5l4.5 4.5L19 7" />
    </svg>
  );
}

export function IconClose({ className }: P) {
  return (
    <svg className={className ?? "nav-icon"} viewBox="0 0 24 24" {...base}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}
