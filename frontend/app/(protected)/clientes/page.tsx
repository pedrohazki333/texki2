import Link from "next/link";

import { ConfirmarExclusao } from "@/components/clientes/confirmar-exclusao";
import { apiServerFetch } from "@/lib/api-server";
import type { Cliente } from "@/lib/tipos";

export const dynamic = "force-dynamic";

export default async function ClientesPage() {
  const res = await apiServerFetch("/clientes");
  if (!res.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar clientes.
      </div>
    );
  }
  const clientes = (await res.json()) as Cliente[];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Clientes</h1>
        <Link
          href="/clientes/novo"
          className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800"
        >
          Novo cliente
        </Link>
      </div>

      {clientes.length === 0 ? (
        <div className="rounded-lg border border-dashed border-neutral-300 bg-white p-10 text-center">
          <p className="text-neutral-700">Nenhum cliente cadastrado ainda.</p>
          <Link
            href="/clientes/novo"
            className="mt-3 inline-block text-sm font-medium text-neutral-900 underline"
          >
            Cadastrar o primeiro
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-neutral-600">
              <tr>
                <th className="px-4 py-2 font-medium">Nome</th>
                <th className="px-4 py-2 font-medium">Telefone</th>
                <th className="px-4 py-2 font-medium">LGPD</th>
                <th className="px-4 py-2 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {clientes.map((c) => {
                const nome = c.ultimo_nome
                  ? `${c.primeiro_nome} ${c.ultimo_nome}`
                  : c.primeiro_nome;
                return (
                  <tr key={c.id} className="border-t border-neutral-100">
                    <td className="px-4 py-2">{nome}</td>
                    <td className="px-4 py-2">{c.telefone}</td>
                    <td className="px-4 py-2">
                      {c.consentimento_lgpd ? (
                        <span
                          title={
                            c.data_consentimento
                              ? `Consentido em ${c.data_consentimento}`
                              : ""
                          }
                          className="text-green-700"
                        >
                          ✓
                        </span>
                      ) : (
                        <span className="text-neutral-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex justify-end gap-2">
                        <Link
                          href={`/clientes/${c.id}/editar`}
                          className="rounded border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100"
                        >
                          Editar
                        </Link>
                        <ConfirmarExclusao clienteId={c.id} nomeCompleto={nome} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
