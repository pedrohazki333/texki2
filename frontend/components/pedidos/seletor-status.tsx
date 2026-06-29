"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { ApiErrorBody, PedidoStatus } from "@/lib/tipos";

const API = "/api";

const OPCOES: { valor: PedidoStatus; rotulo: string }[] = [
  { valor: "recebido", rotulo: "Recebido" },
  { valor: "pago", rotulo: "Pago" },
  { valor: "na_fila_de_impressao", rotulo: "Na fila de impressão" },
  { valor: "impressao_pronta", rotulo: "Impressão pronta" },
  { valor: "pedido_pronto", rotulo: "Pedido pronto" },
  { valor: "entregue", rotulo: "Entregue" },
  { valor: "cancelado", rotulo: "Cancelado" },
];

type Props = {
  pedidoId: number;
  statusAtual: PedidoStatus;
};

export function SeletorStatus({ pedidoId, statusAtual }: Props) {
  const router = useRouter();
  const [valor, setValor] = useState<PedidoStatus>(statusAtual);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function trocar(novo: PedidoStatus) {
    if (novo === valor) return;
    setErro(null);
    setCarregando(true);
    const anterior = valor;
    setValor(novo);
    try {
      const res = await fetch(`${API}/pedidos/${pedidoId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: novo }),
        credentials: "include",
      });
      if (!res.ok) {
        setValor(anterior);
        const body = (await res.json().catch(() => null)) as ApiErrorBody | null;
        setErro(body?.error?.message ?? "Erro ao trocar status.");
        return;
      }
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="space-y-1">
      <select
        value={valor}
        disabled={carregando}
        onChange={(e) => trocar(e.target.value as PedidoStatus)}
        className="w-full rounded border border-neutral-300 bg-white px-2 py-1 text-xs disabled:opacity-50"
      >
        {OPCOES.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.rotulo}
          </option>
        ))}
      </select>
      {erro && <p className="text-[11px] text-red-600">{erro}</p>}
    </div>
  );
}
