import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ApiKeyGate from "@/components/ApiKeyGate";
import Sidebar from "@/components/Sidebar";
import StatusBar from "@/components/StatusBar";
import { ScanProvider } from "@/lib/scan-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "J.A.R.V.I.S.",
  description: "Local AI-powered cybersecurity workstation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ScanProvider>
          <ApiKeyGate>
            <div className="flex min-h-screen">
              <Sidebar />
              <div className="flex-1 flex flex-col min-w-0">
                <StatusBar />
                <main className="flex-1 overflow-y-auto p-6">{children}</main>
              </div>
            </div>
          </ApiKeyGate>
        </ScanProvider>
      </body>
    </html>
  );
}
