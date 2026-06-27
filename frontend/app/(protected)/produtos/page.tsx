import Link from "next/link";

import { apiServerFetch } from "@/lib/api-server";
import type { Produto } from "@/lib/tipos";

export const dynamic = "force-dynamic";

const LABEL_TIPO: Record<string, string> = {
  dtf_por_metro: "DTF por metro",
  vestuario: "Vestuário",
};

export default async function ProdutosPage() {
  const res = await apiServerFetch("/produtos");
  if (!res.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar produtos.
      </div>
    );
  }
  const produtos = (await res.json()) as Produto[];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Produtos</h1>
        <Link
          href="/produtos/novo"
          className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800"
        >
          Novo produto
        </Link>
      </div>

      {produtos.length === 0 ? (
        <div className="rounded-lg border border-dashed border-neutral-300 bg-white p-10 text-center">
          <p className="text-neutral-700">Nenhum produto cadastrado ainda.</p>
          <Link
            href="/produtos/novo"
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
                <th className="px-4 py-2 font-medium">Tipo</th>
                <th className="px-4 py-2 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {produtos.map((p) => (
                <tr key={p.id} className="border-t border-neutral-100">
                  <td className="px-4 py-2">{p.nome}</td>
                  <td className="px-4 py-2 text-neutral-600">
                    {LABEL_TIPO[p.tipo] ?? p.tipo}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      href={`/produtos/${p.id}`}
                      className="rounded border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100"
                    >
                      Abrir
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
