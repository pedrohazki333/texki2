"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { BaseFaixa, FaixaPreco, TipoProduto } from "@/lib/tipos";

const BASE_POR_TIPO: Record<TipoProduto, BaseFaixa> = {
  dtf_por_metro: "comprimento_m",
  vestuario: "quantidade",
};

const LABEL_BASE: Record<BaseFaixa, string> = {
  comprimento_m: "comprimento (m)",
  quantidade: "quantidade",
};

type Props = {
  produtoId: number;
  produtoTipo: TipoProduto;
  faixas: FaixaPreco[];
};

export function FaixasTabela({ produtoId, produtoTipo, faixas }: Props) {
  const router = useRouter();
  const baseFixa = BASE_POR_TIPO[produtoTipo];
  const [min, setMin] = useState("");
  const [max, setMax] = useState("");
  const [preco, setPreco] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function adicionar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (!min.trim() || !preco.trim()) {
      setErro("Mínimo e preço são obrigatórios.");
      return;
    }
    setCarregando(true);
    try {
      const res = await apiClientFetch(`/produtos/${produtoId}/faixas`, {
        method: "POST",
        body: JSON.stringify({
          base: baseFixa,
          min: min.trim(),
          max: max.trim() === "" ? null : max.trim(),
          preco_unitario: preco.trim(),
        }),
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      setMin("");
      setMax("");
      setPreco("");
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  async function excluir(id: number) {
    setErro(null);
    const res = await apiClientFetch(`/produtos/${produtoId}/faixas/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      setErro(res.error.message);
      return;
    }
    router.refresh();
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">
        Faixas de preço{" "}
        <span className="text-sm font-normal text-neutral-500">
          (por {LABEL_BASE[baseFixa]})
        </span>
      </h2>
      <p className="text-xs text-neutral-500">
        Convenção: cada faixa cobre <code>min &lt; medida ≤ max</code>. Deixar
        máximo em branco significa "sem teto".
      </p>

      {faixas.length === 0 ? (
        <p className="text-sm text-neutral-500">Nenhuma faixa cadastrada.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-neutral-600">
              <tr>
                <th className="px-3 py-2 font-medium">Intervalo</th>
                <th className="px-3 py-2 font-medium">Preço unitário</th>
                <th className="px-3 py-2 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {faixas.map((f) => (
                <tr key={f.id} className="border-t border-neutral-100">
                  <td className="px-3 py-2 font-mono">
                    ({f.min}, {f.max ?? "∞"}]
                  </td>
                  <td className="px-3 py-2">R$ {f.preco_unitario}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => excluir(f.id)}
                      className="rounded border border-red-300 px-3 py-1 text-xs text-red-700 hover:bg-red-50"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={adicionar} className="flex flex-wrap items-end gap-2">
        <label className="block">
          <span className="text-xs text-neutral-700">Mín (exclusivo)</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={min}
            onChange={(e) => setMin(e.target.value)}
            className="mt-1 block w-32 rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs text-neutral-700">Máx (inclusivo)</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={max}
            onChange={(e) => setMax(e.target.value)}
            placeholder="(sem teto)"
            className="mt-1 block w-32 rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs text-neutral-700">Preço unitário (R$)</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={preco}
            onChange={(e) => setPreco(e.target.value)}
            className="mt-1 block w-32 rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
        <button
          type="submit"
          disabled={carregando}
          className="rounded bg-neutral-900 px-3 py-1.5 text-sm text-white hover:bg-neutral-800 disabled:opacity-50"
        >
          Adicionar
        </button>
      </form>

      {erro && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {erro}
        </div>
      )}
    </section>
  );
}
