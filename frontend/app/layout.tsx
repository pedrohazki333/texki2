import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "TEXKI2",
  description: "Controle de produção e administração de pedidos DTF",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased">
        {children}
      </body>
    </html>
  );
}
