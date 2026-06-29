import Link from "next/link";

import { CardPedido } from "@/components/pedidos/card-pedido";
import { apiServerFetch } from "@/lib/api-server";
import type { DashboardPedidos, PedidoStatus } from "@/lib/tipos";

export const dynamic = "force-dynamic";

type StatusDashboard = Exclude<PedidoStatus, "cancelado" | "entregue">;

const COLUNAS: { status: StatusDashboard; titulo: string }[] = [
  { status: "recebido", titulo: "Recebido" },
  { status: "pago", titulo: "Pago" },
  { status: "na_fila_de_impressao", titulo: "Na fila de impressão" },
  { status: "impressao_pronta", titulo: "Impressão pronta" },
  { status: "pedido_pronto", titulo: "Pedido pronto" },
];

export default async function PedidosDashboardPage() {
  const res = await apiServerFetch("/pedidos/dashboard");
  if (!res.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar o dashboard de pedidos.
      </div>
    );
  }
  const dashboard = (await res.json()) as DashboardPedidos;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard de pedidos</h1>
          <p className="text-sm text-neutral-600">
            Pedidos agrupados por status. Cancelados ficam fora — veja em{" "}
            <Link href="/pedidos/lista" className="underline">
              lista completa
            </Link>
            .
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/pedidos/lista"
            className="rounded border border-neutral-300 px-3 py-2 text-sm hover:bg-neutral-100"
          >
            Lista completa
          </Link>
          <Link
            href="/pedidos/novo"
            className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800"
          >
            Novo pedido
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {COLUNAS.map((col) => {
          const pedidos = dashboard[col.status] ?? [];
          return (
            <section
              key={col.status}
              className="flex flex-col gap-2 rounded-lg bg-neutral-100 p-3"
            >
              <header className="flex items-baseline justify-between">
                <h2 className="text-sm font-semibold text-neutral-800">
                  {col.titulo}
                </h2>
                <span className="rounded bg-white px-2 py-0.5 text-xs text-neutral-600">
                  {pedidos.length}
                </span>
              </header>
              {pedidos.length === 0 ? (
                <p className="rounded border border-dashed border-neutral-300 px-2 py-6 text-center text-xs text-neutral-500">
                  Nenhum pedido aqui.
                </p>
              ) : (
                <div className="flex flex-col gap-2">
                  {pedidos.map((p) => (
                    <CardPedido key={p.id} pedido={p} />
                  ))}
                </div>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
