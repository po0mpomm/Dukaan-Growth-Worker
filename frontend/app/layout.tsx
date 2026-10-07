import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Dukaan Growth Worker | दुकान ग्रोथ वर्कर",
  description:
    "Local-first, privacy-safe AI Worker helping kirana and small retail owners review monthly business activity, identify weak areas, create follow-up actions, and track month-on-month growth.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
