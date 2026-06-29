import Link from "next/link";

import { SeletorStatus } from "@/components/pedidos/seletor-status";
import type { PedidoCard } from "@/lib/tipos";

function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export function CardPedido({ pedido }: { pedido: PedidoCard }) {
  const temThumbPng =
    pedido.primeira_arte_id !== null && pedido.primeira_arte_mime === "image/png";

  return (
    <article className="flex gap-3 rounded-lg border border-neutral-200 bg-white p-3 shadow-sm">
      <div className="h-20 w-20 shrink-0 overflow-hidden rounded border border-neutral-200 bg-neutral-50">
        {temThumbPng ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={`/api/pedidos/${pedido.id}/artes/${pedido.primeira_arte_id}/thumb`}
            alt={`Arte do pedido #${pedido.id}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-[10px] uppercase text-neutral-400">
            {pedido.primeira_arte_id === null
              ? "sem arte"
              : pedido.primeira_arte_mime?.split("/")[1] ?? "?"}
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 text-sm">
        <div className="flex items-baseline justify-between">
          <span className="font-mono text-xs text-neutral-500">#{pedido.id}</span>
          <span className="text-xs text-neutral-500">
            {formatarData(pedido.data_entrega)}
          </span>
        </div>
        <div className="truncate font-medium" title={pedido.cliente_nome}>
          {pedido.cliente_nome}
        </div>
        <div className="text-xs text-neutral-600">R$ {pedido.total}</div>
        <div className="mt-1 flex items-center gap-2">
          <Link
            href={`/pedidos/${pedido.id}`}
            className="rounded border border-neutral-300 px-2 py-0.5 text-xs hover:bg-neutral-100"
          >
            Abrir
          </Link>
          <div className="flex-1">
            <SeletorStatus pedidoId={pedido.id} statusAtual={pedido.status} />
          </div>
        </div>
      </div>
    </article>
  );
}
