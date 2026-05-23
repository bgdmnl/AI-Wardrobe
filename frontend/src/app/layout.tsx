import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Wardrobe Tracker",
  description: "AI-powered wardrobe management - organize, tag, and track your clothing collection",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0f172a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full">
      <body className="font-sans antialiased bg-slate-950 text-slate-50 min-h-full flex flex-col tracking-tight">
        <div className="w-full min-h-screen flex flex-col bg-slate-950 md:shadow-2xl md:border-x md:border-slate-900 md:mx-auto md:max-w-6xl">
          {children}
        </div>
        <Toaster />
      </body>
    </html>
  );
}
