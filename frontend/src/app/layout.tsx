import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gradient Fisherman — SMB Data Assistant",
  description:
    "Ask your business data questions in plain English. Powered by DigitalOcean Gradient™ AI and Claude Sonnet 4.6.",
  openGraph: {
    title: "Gradient Fisherman",
    description: "AI-powered data analysis for small businesses",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
