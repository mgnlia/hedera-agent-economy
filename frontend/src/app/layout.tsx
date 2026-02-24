import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hedera Agent Economy | AI Agent Coordination Layer",
  description:
    "Multi-agent coordination layer using Hedera Consensus Service. Agents discover, negotiate, and settle micropayments in HBAR.",
  openGraph: {
    title: "Hedera Agent Economy",
    description: "Live AI agent marketplace powered by Hedera Consensus Service",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
