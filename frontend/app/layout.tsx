import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { ClientProvider } from "@/components/client-provider";

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "BotArmy - AI Agent Orchestration",
  description: "Multi-agent AI orchestration system for autonomous product generation",
  generator: "v0.app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={dmSans.variable} suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ClientProvider>
          {children}
        </ClientProvider>
      </body>
    </html>
  );
}