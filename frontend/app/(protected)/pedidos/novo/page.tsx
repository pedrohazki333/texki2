import Link from "next/link";

import { PedidoForm } from "@/components/pedidos/pedido-form";
import { apiServerFetch } from "@/lib/api-server";
import type { Cliente, ProdutoDetalhes } from "@/lib/tipos";

export const dynamic = "force-dynamic";

export default async function NovoPedidoPage() {
  const [resClientes, resProdutos] = await Promise.all([
    apiServerFetch("/clientes"),
    apiServerFetch("/produtos"),
  ]);
  if (!resClientes.ok || !resProdutos.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar clientes ou produtos.
      </div>
    );
  }
  const clientes = (await resClientes.json()) as Cliente[];
  const produtosRaw = (await resProdutos.json()) as Array<{
    id: number;
    nome: string;
    tipo: "vestuario" | "dtf_por_metro";
  }>;
  // Para o seletor, precisamos das variações de cada produto: faz uma chamada
  // detalhada por produto. Para a Fatia 3 isso é ok (~10 produtos no catálogo);
  // se crescer muito, vira um endpoint resumido próprio.
  const produtosDetalhados = (await Promise.all(
    produtosRaw.map(async (p) => {
      const res = await apiServerFetch(`/produtos/${p.id}`);
      if (!res.ok) return null;
      return (await res.json()) as ProdutoDetalhes;
    }),
  )).filter((p): p is ProdutoDetalhes => p !== null);

  return (
    <div className="space-y-4">
      <div className="text-sm text-neutral-500">
        <Link href="/pedidos" className="hover:underline">
          Pedidos
        </Link>{" "}
        / Novo
      </div>
      <h1 className="text-2xl font-semibold">Novo pedido</h1>
      <PedidoForm modo="criar" clientes={clientes} produtos={produtosDetalhados} />
    </div>
  );
}
