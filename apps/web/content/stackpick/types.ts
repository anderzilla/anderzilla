export type ComparisonRow = {
  feature: string;
  a: string;
  b: string;
};

export type ProsCons = {
  pros: string[];
  cons: string[];
};

export type FaqItem = {
  q: string;
  a: string;
};

export type StackPickComparison = {
  slug: string;
  title: string;
  category: string;
  teaser: string;
  /** ISO date YYYY-MM-DD */
  updated: string;
  author: string;
  productA: {
    id: string;
    name: string;
  };
  productB: {
    id: string;
    name: string;
  };
  tldr: string;
  verdictWinner: "a" | "b" | "tie";
  verdictLabel: string;
  rows: ComparisonRow[];
  a: ProsCons;
  b: ProsCons;
  faq: FaqItem[];
  notes?: string[];
};
