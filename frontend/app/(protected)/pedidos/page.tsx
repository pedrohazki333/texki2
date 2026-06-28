import Link from "next/link";

import { apiServerFetch } from "@/lib/api-server";
import type { Cliente, Pedido } from "@/lib/tipos";

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

function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export default async function PedidosPage() {
  const [resPedidos, resClientes] = await Promise.all([
    apiServerFetch("/pedidos"),
    apiServerFetch("/clientes"),
  ]);
  if (!resPedidos.ok || !resClientes.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar pedidos.
      </div>
    );
  }
  const pedidos = (await resPedidos.json()) as Pedido[];
  const clientes = (await resClientes.json()) as Cliente[];
  const nomePorCliente = new Map(
    clientes.map((c) => [
      c.id,
      c.ultimo_nome ? `${c.primeiro_nome} ${c.ultimo_nome}` : c.primeiro_nome,
    ]),
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Pedidos</h1>
        <Link
          href="/pedidos/novo"
          className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800"
        >
          Novo pedido
        </Link>
      </div>

      {pedidos.length === 0 ? (
        <div className="rounded-lg border border-dashed border-neutral-300 bg-white p-10 text-center">
          <p className="text-neutral-700">Nenhum pedido registrado ainda.</p>
          <Link
            href="/pedidos/novo"
            className="mt-3 inline-block text-sm font-medium text-neutral-900 underline"
          >
            Registrar o primeiro
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-neutral-600">
              <tr>
                <th className="px-4 py-2 font-medium">#</th>
                <th className="px-4 py-2 font-medium">Cliente</th>
                <th className="px-4 py-2 font-medium">Entrega</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium text-right">Total</th>
                <th className="px-4 py-2 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {pedidos.map((p) => (
                <tr key={p.id} className="border-t border-neutral-100">
                  <td className="px-4 py-2 font-mono">{p.id}</td>
                  <td className="px-4 py-2">
                    {nomePorCliente.get(p.cliente_id) ?? `Cliente #${p.cliente_id}`}
                  </td>
                  <td className="px-4 py-2">{formatarData(p.data_entrega)}</td>
                  <td className="px-4 py-2 text-neutral-700">
                    {LABEL_STATUS[p.status] ?? p.status}
                  </td>
                  <td className="px-4 py-2 text-right">R$ {p.total}</td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      href={`/pedidos/${p.id}`}
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
