import Link from "next/link";
import { redirect } from "next/navigation";

import { LogoutButton } from "@/components/logout-button";
import { apiServerFetch } from "@/lib/api-server";
import type { Role, UsuarioAtual } from "@/lib/tipos";

const ITENS_NAV: Array<{ label: string; href: string; papeis: Role[] }> = [
  { label: "Clientes", href: "/clientes", papeis: ["vendedora", "administrador"] },
];

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const res = await apiServerFetch("/auth/me");
  if (!res.ok) {
    redirect("/login");
  }
  const user = (await res.json()) as UsuarioAtual;
  const itens = ITENS_NAV.filter((i) => i.papeis.includes(user.role));

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b bg-white px-6 py-3">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="font-semibold">
            TEXKI2
          </Link>
          <nav className="flex gap-4 text-sm">
            {itens.map((i) => (
              <Link
                key={i.href}
                href={i.href}
                className="text-neutral-600 hover:text-neutral-900"
              >
                {i.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-neutral-600">
            {user.nome} <span className="text-neutral-400">({user.role})</span>
          </span>
          <LogoutButton />
        </div>
      </header>
      <main className="p-6">{children}</main>
    </div>
  );
}
