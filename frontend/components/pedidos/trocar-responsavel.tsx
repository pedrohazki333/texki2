"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { ResponsavelPossivel } from "@/lib/tipos";

type Props = {
  pedidoId: number;
  vendedoraAtualId: number;
  vendedoras: ResponsavelPossivel[];
};

export function TrocarResponsavel({
  pedidoId,
  vendedoraAtualId,
  vendedoras,
}: Props) {
  const router = useRouter();
  const [selecionado, setSelecionado] = useState<number>(vendedoraAtualId);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function salvar() {
    setCarregando(true);
    setErro(null);
    setOk(false);
    try {
      const res = await apiClientFetch(`/pedidos/${pedidoId}/responsavel`, {
        method: "PUT",
        body: JSON.stringify({ vendedora_id: selecionado }),
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      setOk(true);
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <section className="space-y-2 rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-4">
      <h2 className="text-lg font-semibold">Responsável (Admin)</h2>
      <p className="text-xs text-neutral-600">
        Trocar o responsável é restrito ao administrador e fica registrado em auditoria.
      </p>
      <div className="flex flex-wrap items-end gap-2">
        <label className="block">
          <span className="text-xs text-neutral-700">Vendedora/Admin</span>
          <select
            value={selecionado}
            onChange={(e) => setSelecionado(Number(e.target.value))}
            className="mt-1 block w-64 rounded border border-neutral-300 px-3 py-1.5 text-sm"
          >
            {vendedoras.map((v) => (
              <option key={v.id} value={v.id}>
                {v.nome} ({v.role})
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={carregando || selecionado === vendedoraAtualId}
          onClick={salvar}
          className="rounded bg-neutral-900 px-3 py-1.5 text-sm text-white hover:bg-neutral-800 disabled:opacity-50"
        >
          {carregando ? "Salvando…" : "Trocar responsável"}
        </button>
      </div>
      {ok && (
        <p className="text-xs text-green-700">Responsável atualizado.</p>
      )}
      {erro && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {erro}
        </div>
      )}
    </section>
  );
}
