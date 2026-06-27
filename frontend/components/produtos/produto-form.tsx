"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { Produto, TipoProduto } from "@/lib/tipos";

export function ProdutoForm() {
  const router = useRouter();
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState<TipoProduto>("vestuario");
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    if (!nome.trim()) {
      setErro("Nome é obrigatório.");
      return;
    }
    setCarregando(true);
    try {
      const res = await apiClientFetch<Produto>("/produtos", {
        method: "POST",
        body: JSON.stringify({ nome: nome.trim(), tipo }),
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      router.push(`/produtos/${res.data.id}`);
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <label className="block">
        <span className="text-sm text-neutral-700">
          Nome <span className="text-red-600">*</span>
        </span>
        <input
          type="text"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          maxLength={120}
          className="mt-1 w-full rounded border border-neutral-300 px-3 py-2 focus:border-neutral-500 focus:outline-none"
        />
      </label>

      <label className="block">
        <span className="text-sm text-neutral-700">Tipo</span>
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoProduto)}
          className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
        >
          <option value="vestuario">Vestuário</option>
          <option value="dtf_por_metro">DTF por metro</option>
        </select>
        <span className="mt-1 block text-xs text-neutral-500">
          O tipo não pode ser alterado depois de salvo.
        </span>
      </label>

      {erro && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {erro}
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={carregando}
          className="rounded bg-neutral-900 px-4 py-2 text-sm text-white hover:bg-neutral-800 disabled:opacity-50"
        >
          {carregando ? "Salvando…" : "Salvar"}
        </button>
        <button
          type="button"
          onClick={() => router.push("/produtos")}
          className="rounded border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-100"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
