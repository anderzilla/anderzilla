import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { StackPickComparisonView } from "@/components/StackPickComparison";
import { SITE } from "../../../../content/affiliates";
import {
  getComparison,
  listComparisons,
} from "../../../../content/stackpick";

type Props = { params: Promise<{ slug: string }> };

export function generateStaticParams() {
  return listComparisons().map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const data = getComparison(slug);
  if (!data) return { title: "Comparison" };
  return {
    title: data.title,
    description: data.teaser,
    openGraph: {
      title: `${data.title} · StackPick`,
      description: data.teaser,
      url: `${SITE.url}/stackpick/${data.slug}`,
    },
  };
}

export default async function StackPickComparisonPage({ params }: Props) {
  const { slug } = await params;
  const data = getComparison(slug);
  if (!data) notFound();
  return <StackPickComparisonView data={data} />;
}
