import { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "danger";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  full?: boolean;
}

const styles: Record<Variant, React.CSSProperties> = {
  primary: { background: "var(--accent)", color: "var(--on-accent)" },
  ghost: {
    background: "transparent",
    color: "var(--text)",
    border: "1px solid var(--border)",
  },
  danger: { background: "var(--danger)", color: "var(--on-accent)" },
};

export function Button({ variant = "primary", full, style, ...rest }: Props) {
  return (
    <button
      {...rest}
      style={{
        appearance: "none",
        border: "none",
        borderRadius: "var(--radius)",
        padding: "13px 18px",
        fontSize: "0.95rem",
        fontWeight: 700,
        cursor: rest.disabled ? "default" : "pointer",
        opacity: rest.disabled ? 0.5 : 1,
        width: full ? "100%" : undefined,
        transition: "transform .05s ease, background .15s ease",
        ...styles[variant],
        ...style,
      }}
    />
  );
}
