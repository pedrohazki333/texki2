"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";

type Props = {
  id: number;
  nomeAtual: string;
};

export function NomeProdutoEditavel({ id, nomeAtual }: Props) {
  const router = useRouter();
  const [editando, setEditando] = useState(false);
  const [nome, setNome] = useState(nomeAtual);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function salvar() {
    setErro(null);
    if (!nome.trim()) {
      setErro("Nome é obrigatório.");
      return;
    }
    setCarregando(true);
    try {
      const res = await apiClientFetch(`/produtos/${id}`, {
        method: "PUT",
        body: JSON.stringify({ nome: nome.trim() }),
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      setEditando(false);
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  function cancelar() {
    setNome(nomeAtual);
    setEditando(false);
    setErro(null);
  }

  if (!editando) {
    return (
      <div className="flex items-center gap-2">
        <h1 className="text-2xl font-semibold">{nomeAtual}</h1>
        <button
          type="button"
          onClick={() => setEditando(true)}
          className="rounded border border-neutral-300 px-2 py-0.5 text-xs hover:bg-neutral-100"
        >
          Editar
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        type="text"
        value={nome}
        onChange={(e) => setNome(e.target.value)}
        maxLength={120}
        className="rounded border border-neutral-300 px-2 py-1 text-lg"
      />
      <button
        type="button"
        onClick={salvar}
        disabled={carregando}
        className="rounded bg-neutral-900 px-3 py-1 text-xs text-white hover:bg-neutral-800 disabled:opacity-50"
      >
        Salvar
      </button>
      <button
        type="button"
        onClick={cancelar}
        className="rounded border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100"
      >
        Cancelar
      </button>
      {erro && <span className="text-xs text-red-600">{erro}</span>}
    </div>
  );
}
