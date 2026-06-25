import { redirect } from "next/navigation";

import { LogoutButton } from "@/components/logout-button";
import { apiServerFetch } from "@/lib/api-server";

type Usuario = {
  id: number;
  email: string;
  nome: string;
  role: "vendedora" | "impressor" | "administrador";
};

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const res = await apiServerFetch("/auth/me");
  if (!res.ok) {
    redirect("/login");
  }
  const user = (await res.json()) as Usuario;

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b bg-white px-6 py-3">
        <span className="font-semibold">TEXKI2</span>
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
