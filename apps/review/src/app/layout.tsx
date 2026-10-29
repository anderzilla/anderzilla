import type { Metadata } from 'next';
import { Oxanium, Space_Grotesk } from 'next/font/google';
import './globals.css';

const display = Oxanium({ subsets: ['latin'], variable: '--display' });
const body = Space_Grotesk({ subsets: ['latin'], variable: '--body' });

export const metadata: Metadata = {
  title: 'Revisão AnderZilla',
  description: 'Revisão e aprovação de conteúdo preparado por agentes de IA',
  robots: { index: false, follow: false },
  icons: { icon: '/brand/favicon.svg', apple: '/brand/apple-touch-icon.png' },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={`${display.variable} ${body.variable}`}>{children}</body>
    </html>
  );
}
