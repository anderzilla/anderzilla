import { AFFILIATE_DISCLOSURE } from "../../content/affiliates";

type Props = {
  className?: string;
  compact?: boolean;
};

export function AffiliateDisclosure({ className = "", compact = false }: Props) {
  return (
    <aside
      className={`rounded-xl border border-amber-glow/20 bg-amber-glow/5 px-4 py-3 text-sm text-zinc-300 ${className}`}
      role="note"
    >
      <p className="font-medium text-amber-soft">Affiliate disclosure</p>
      <p className={`mt-1 text-zinc-400 ${compact ? "text-xs leading-relaxed" : ""}`}>
        {AFFILIATE_DISCLOSURE}
      </p>
    </aside>
  );
}
