import { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
};

const variants: Record<NonNullable<Props["variant"]>, string> = {
  primary:
    "bg-amber-500 text-zinc-950 hover:bg-amber-400 shadow-lg shadow-amber-500/20",
  secondary:
    "bg-zinc-800 text-zinc-50 hover:bg-zinc-700 border border-zinc-700",
  ghost: "bg-transparent text-zinc-300 hover:bg-zinc-800/60",
};

const sizes: Record<NonNullable<Props["size"]>, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

export function buttonStyles({
  className = "",
  variant = "primary",
  size = "md",
}: Pick<Props, "className" | "variant" | "size"> = {}) {
  return `inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400 disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`;
}

export function Button({
  className = "",
  variant = "primary",
  size = "md",
  ...props
}: Props) {
  return (
    <button className={buttonStyles({ variant, size, className })} {...props} />
  );
}
