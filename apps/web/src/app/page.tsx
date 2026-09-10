import type { Metadata } from "next";
import Hub from "@/components/hub/Hub";
export const metadata: Metadata = {
  title: "AnderZilla — Games, IA e boas descobertas",
  description:
    "Explore games, IA, gadgets e curiosidades com o Ghost. Seu radar de descobertas, desafios, lives e Karaca Points.",
};
export default function HomePage() {
  return <Hub />;
}
