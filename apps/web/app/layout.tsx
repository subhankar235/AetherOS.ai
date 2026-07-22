import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "@/styles/globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Aether — The AI Chief of Staff for Your Inbox",
  description:
    "The first AI Chief of Staff that watches, triages, and prepares — but only acts on your command.",
  openGraph: {
    title: "Aether — AI Chief of Staff",
    description:
      "Your inbox, autonomously refined. The first AI Chief of Staff that watches, triages, and prepares — but only acts on your command.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
    >
      <html
        lang="en"
        className={`${inter.variable} ${jetbrainsMono.variable} dark`}
        suppressHydrationWarning
        data-scroll-behavior="smooth"
      >
        <body className="min-h-screen font-sans antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}
