import type { Metadata } from "next";
import { MemberArea } from "@/components/account/MemberArea";

export const metadata: Metadata = {
  title: "Painel do Jogador / Player Dashboard — AnderZilla",
  robots: {
    index: false,
    follow: false,
    nocache: true,
  },
};

export default function AccountPage() {
  return <MemberArea lang="pt" view="dashboard" />;
}
