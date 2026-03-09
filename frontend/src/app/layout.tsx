import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsiderFlow - Insider Trading Dashboard",
  description: "Track insider stock sales and purchases across U.S. public companies",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-white">
              InsiderFlow
            </Link>
            <div className="flex gap-6 text-sm text-gray-400">
              <Link href="/" className="hover:text-white transition-colors">
                Dashboard
              </Link>
              <Link href="/alerts" className="hover:text-white transition-colors">
                Alerts
              </Link>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
