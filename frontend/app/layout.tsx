import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Hunter Dashboard",
  description: "7-agent AI-powered job search assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-6">
          <span className="font-bold text-blue-400">Job Hunter</span>
          <a href="/" className="text-sm text-gray-400 hover:text-white">Dashboard</a>
          <a href="/jobs" className="text-sm text-gray-400 hover:text-white">Jobs</a>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
