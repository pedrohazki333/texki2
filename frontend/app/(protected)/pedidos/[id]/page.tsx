import Link from "next/link";
import { notFound } from "next/navigation";

import { ArtesPainel } from "@/components/pedidos/artes-painel";
import { ExcluirPedido } from "@/components/pedidos/excluir-pedido";
import { HistoricoAuditoria } from "@/components/pedidos/historico-auditoria";
import { PedidoForm } from "@/components/pedidos/pedido-form";
import { SeletorStatus } from "@/components/pedidos/seletor-status";
import { TrocarResponsavel } from "@/components/pedidos/trocar-responsavel";
import { apiServerFetch } from "@/lib/api-server";
import type {
  Cliente,
  PedidoDetalhes,
  ProdutoDetalhes,
  ResponsavelPossivel,
  UsuarioAtual,
} from "@/lib/tipos";

export const dynamic = "force-dynamic";

const LABEL_STATUS: Record<string, string> = {
  recebido: "Recebido",
  pago: "Pago",
  na_fila_de_impressao: "Na fila de impressão",
  impressao_pronta: "Impressão pronta",
  pedido_pronto: "Pedido pronto",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

export default async function PedidoDetalhesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [resPedido, resClientes, resProdutos, resMe, resVend] = await Promise.all([
    apiServerFetch(`/pedidos/${id}`),
    apiServerFetch("/clientes"),
    apiServerFetch("/produtos"),
    apiServerFetch("/auth/me"),
    apiServerFetch("/pedidos/_utils/vendedoras"),
  ]);

  if (resPedido.status === 404) notFound();
  if (!resPedido.ok || !resClientes.ok || !resProdutos.ok || !resMe.ok || !resVend.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar pedido.
      </div>
    );
  }
  const pedido = (await resPedido.json()) as PedidoDetalhes;
  const clientes = (await resClientes.json()) as Cliente[];
  const produtosRaw = (await resProdutos.json()) as Array<{ id: number }>;
  const produtosDetalhados = (await Promise.all(
    produtosRaw.map(async (p) => {
      const r = await apiServerFetch(`/produtos/${p.id}`);
      if (!r.ok) return null;
      return (await r.json()) as ProdutoDetalhes;
    }),
  )).filter((p): p is ProdutoDetalhes => p !== null);
  const me = (await resMe.json()) as UsuarioAtual;
  const vendedoras = (await resVend.json()) as ResponsavelPossivel[];
  const responsavel = vendedoras.find((v) => v.id === pedido.vendedora_id);

  return (
    <div className="space-y-6">
      <div className="text-sm text-neutral-500">
        <Link href="/pedidos" className="hover:underline">
          Pedidos
        </Link>{" "}
        / #{pedido.id}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Pedido #{pedido.id}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-600">
            <span>Status:</span>
            <div className="w-56">
              <SeletorStatus pedidoId={pedido.id} statusAtual={pedido.status} />
            </div>
            <span className="text-xs text-neutral-400">
              ({LABEL_STATUS[pedido.status] ?? pedido.status})
            </span>
          </div>
          <p className="text-sm text-neutral-600">
            Responsável:{" "}
            <span className="font-medium">
              {responsavel?.nome ?? `#${pedido.vendedora_id}`}
            </span>
          </p>
        </div>
        <ExcluirPedido pedidoId={pedido.id} />
      </div>

      <PedidoForm
        modo="editar"
        clientes={clientes}
        produtos={produtosDetalhados}
        inicial={pedido}
      />

      <ArtesPainel pedidoId={pedido.id} artes={pedido.artes} />

      {me.role === "administrador" && (
        <TrocarResponsavel
          pedidoId={pedido.id}
          vendedoraAtualId={pedido.vendedora_id}
          vendedoras={vendedoras}
        />
      )}

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Histórico</h2>
        <HistoricoAuditoria pedidoId={pedido.id} />
      </section>
    </div>
  );
}
