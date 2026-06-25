import Link from "next/link";
import { notFound } from "next/navigation";

import { ClienteForm } from "@/components/clientes/cliente-form";
import { apiServerFetch } from "@/lib/api-server";
import type { Cliente } from "@/lib/tipos";

export const dynamic = "force-dynamic";

export default async function EditarClientePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await apiServerFetch(`/clientes/${id}`);

  if (res.status === 404) notFound();
  if (!res.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar cliente.
      </div>
    );
  }
  const cliente = (await res.json()) as Cliente;
  const nome = cliente.ultimo_nome
    ? `${cliente.primeiro_nome} ${cliente.ultimo_nome}`
    : cliente.primeiro_nome;

  return (
    <div className="space-y-4">
      <div className="text-sm text-neutral-500">
        <Link href="/clientes" className="hover:underline">
          Clientes
        </Link>{" "}
        / Editar
      </div>
      <h1 className="text-2xl font-semibold">Editar {nome}</h1>
      <ClienteForm modo="editar" inicial={cliente} />
    </div>
  );
}
