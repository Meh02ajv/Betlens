import { Providers } from "./providers";
import type { Metadata, Viewport } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: {
    default: "BetLens — Sports Analytics & Probability",
    template: "%s | BetLens",
  },
  description:
    "Understand the real statistical chances of sporting events. Football and NBA probabilities, odds comparison, and AI-powered analysis.",
  keywords: ["sports analytics", "football predictions", "NBA predictions", "betting odds"],
  robots: { index: true, follow: true },
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0B2545",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}