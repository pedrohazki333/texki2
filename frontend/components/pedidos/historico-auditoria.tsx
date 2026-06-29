import { apiServerFetch } from "@/lib/api-server";
import type { AuditoriaItem, ResponsavelPossivel } from "@/lib/tipos";

const LABEL_STATUS: Record<string, string> = {
  recebido: "Recebido",
  pago: "Pago",
  na_fila_de_impressao: "Na fila de impressão",
  impressao_pronta: "Impressão pronta",
  pedido_pronto: "Pedido pronto",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

function formatarMomento(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function descrever(
  item: AuditoriaItem,
  nomePorUsuario: Map<number, string>,
): string {
  const quem = nomePorUsuario.get(item.usuario_id) ?? `usuário #${item.usuario_id}`;
  if (item.campo === "status") {
    const antes = LABEL_STATUS[item.valor_anterior ?? ""] ?? item.valor_anterior;
    const depois = LABEL_STATUS[item.valor_novo ?? ""] ?? item.valor_novo;
    return `${quem} alterou status: ${antes} → ${depois}`;
  }
  if (item.campo === "vendedora_id") {
    const antes =
      nomePorUsuario.get(Number(item.valor_anterior)) ??
      `#${item.valor_anterior}`;
    const depois =
      nomePorUsuario.get(Number(item.valor_novo)) ?? `#${item.valor_novo}`;
    return `${quem} trocou o responsável: ${antes} → ${depois}`;
  }
  return `${quem} alterou ${item.campo}: ${item.valor_anterior} → ${item.valor_novo}`;
}

export async function HistoricoAuditoria({ pedidoId }: { pedidoId: number }) {
  const [resAudit, resVend] = await Promise.all([
    apiServerFetch(`/pedidos/${pedidoId}/auditoria`),
    apiServerFetch("/pedidos/_utils/vendedoras"),
  ]);
  if (!resAudit.ok) {
    return (
      <p className="text-xs text-neutral-500">
        Não foi possível carregar o histórico.
      </p>
    );
  }
  const itens = (await resAudit.json()) as AuditoriaItem[];
  const vendedoras = resVend.ok
    ? ((await resVend.json()) as ResponsavelPossivel[])
    : [];
  const nomePorUsuario = new Map(vendedoras.map((v) => [v.id, v.nome]));

  if (itens.length === 0) {
    return (
      <p className="text-xs text-neutral-500">
        Nenhuma alteração registrada ainda.
      </p>
    );
  }

  return (
    <ol className="space-y-1 text-sm">
      {itens.map((item) => (
        <li
          key={item.id}
          className="flex flex-wrap items-baseline gap-x-3 border-l-2 border-neutral-200 pl-3"
        >
          <span className="text-xs text-neutral-500">
            {formatarMomento(item.created_at)}
          </span>
          <span>{descrever(item, nomePorUsuario)}</span>
        </li>
      ))}
    </ol>
  );
}
