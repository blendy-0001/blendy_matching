import { InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from "react";

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.82rem",
  fontWeight: 600,
  margin: "14px 0 6px",
  color: "var(--text-muted)",
};

const controlStyle: React.CSSProperties = {
  width: "100%",
  padding: "12px 13px",
  background: "var(--surface-raised)",
  color: "var(--text)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  fontSize: "0.95rem",
  outline: "none",
};

export function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label style={{ display: "block" }}>
      <span style={labelStyle}>
        {label}
        {required && <span style={{ color: "var(--accent)" }}> *</span>}
      </span>
      {children}
    </label>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} style={{ ...controlStyle, ...props.style }} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} style={{ ...controlStyle, ...props.style }} />;
}

export function Textarea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement>,
) {
  return (
    <textarea
      {...props}
      style={{ ...controlStyle, minHeight: 120, resize: "vertical", ...props.style }}
    />
  );
}
