"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { Variacao } from "@/lib/tipos";

type Props = {
  produtoId: number;
  variacoes: Variacao[];
};

export function VariacoesTabela({ produtoId, variacoes }: Props) {
  const router = useRouter();
  const [cor, setCor] = useState("");
  const [tamanho, setTamanho] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function adicionar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (!cor.trim() || !tamanho.trim()) {
      setErro("Cor e tamanho são obrigatórios.");
      return;
    }
    setCarregando(true);
    try {
      const res = await apiClientFetch(`/produtos/${produtoId}/variacoes`, {
        method: "POST",
        body: JSON.stringify({ cor: cor.trim(), tamanho: tamanho.trim() }),
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      setCor("");
      setTamanho("");
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  async function excluir(id: number) {
    setErro(null);
    const res = await apiClientFetch(`/produtos/${produtoId}/variacoes/${id}`, {
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
      <h2 className="text-lg font-semibold">Variações</h2>

      {variacoes.length === 0 ? (
        <p className="text-sm text-neutral-500">Nenhuma variação cadastrada.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-neutral-50 text-left text-neutral-600">
              <tr>
                <th className="px-3 py-2 font-medium">Cor</th>
                <th className="px-3 py-2 font-medium">Tamanho</th>
                <th className="px-3 py-2 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {variacoes.map((v) => (
                <tr key={v.id} className="border-t border-neutral-100">
                  <td className="px-3 py-2">{v.cor}</td>
                  <td className="px-3 py-2">{v.tamanho}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      type="button"
                      onClick={() => excluir(v.id)}
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
          <span className="text-xs text-neutral-700">Cor</span>
          <input
            type="text"
            value={cor}
            onChange={(e) => setCor(e.target.value)}
            maxLength={60}
            className="mt-1 block rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs text-neutral-700">Tamanho</span>
          <input
            type="text"
            value={tamanho}
            onChange={(e) => setTamanho(e.target.value)}
            maxLength={20}
            className="mt-1 block rounded border border-neutral-300 px-3 py-1.5 text-sm"
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
