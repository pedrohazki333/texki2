"use client";

import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { PrecoSelecionado } from "@/lib/tipos";

type Props = {
  produtoId: number;
};

export function CalculadoraPreco({ produtoId }: Props) {
  const [medida, setMedida] = useState("");
  const [resultado, setResultado] = useState<PrecoSelecionado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function consultar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setResultado(null);
    if (!medida.trim()) return;
    setCarregando(true);
    try {
      const res = await apiClientFetch<PrecoSelecionado>(
        `/produtos/${produtoId}/preco?medida=${encodeURIComponent(medida.trim())}`,
      );
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      setResultado(res.data);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <section className="space-y-3 rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-4">
      <h2 className="text-lg font-semibold">Calculadora rápida</h2>
      <p className="text-xs text-neutral-600">
        Informe uma medida (comprimento em metros ou quantidade) para ver qual
        faixa se aplica.
      </p>
      <form onSubmit={consultar} className="flex flex-wrap items-end gap-2">
        <label className="block">
          <span className="text-xs text-neutral-700">Medida</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={medida}
            onChange={(e) => setMedida(e.target.value)}
            className="mt-1 block w-32 rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
        <button
          type="submit"
          disabled={carregando || !medida.trim()}
          className="rounded bg-neutral-900 px-3 py-1.5 text-sm text-white hover:bg-neutral-800 disabled:opacity-50"
        >
          Consultar
        </button>
      </form>

      {resultado && (
        <div className="rounded border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          Faixa #{resultado.faixa_id} — R$ {resultado.preco_unitario} por
          unidade.
        </div>
      )}
      {erro && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {erro}
        </div>
      )}
    </section>
  );
}
