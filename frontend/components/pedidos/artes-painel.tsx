"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { ApiErrorBody, Arte } from "@/lib/tipos";

type AnaliseResp = {
  mime: string;
  proporcao: string | null;
  cadeado: "fechado" | "aberto";
};

type Props = {
  pedidoId: number;
  artes: Arte[];
};

const API = "/api";

function arredondarMm(n: number): number {
  return Math.round(n * 10) / 10;
}

export function ArtesPainel({ pedidoId, artes }: Props) {
  const router = useRouter();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [analise, setAnalise] = useState<AnaliseResp | null>(null);
  const [largura, setLargura] = useState("");
  const [altura, setAltura] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [observacoes, setObservacoes] = useState("");
  const [cadeadoFechado, setCadeadoFechado] = useState(true);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function reset() {
    setArquivo(null);
    setAnalise(null);
    setLargura("");
    setAltura("");
    setQuantidade("1");
    setObservacoes("");
    setCadeadoFechado(true);
    setErro(null);
  }

  async function aoEscolherArquivo(f: File | null) {
    setErro(null);
    setAnalise(null);
    setArquivo(f);
    setLargura("");
    setAltura("");
    if (!f) return;
    setCarregando(true);
    try {
      const fd = new FormData();
      fd.append("arquivo", f);
      const res = await fetch(`${API}/pedidos/${pedidoId}/artes/analisar`, {
        method: "POST",
        body: fd,
        credentials: "include",
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const msg =
          (body as ApiErrorBody | null)?.error?.message ??
          "Erro ao analisar arquivo.";
        setErro(msg);
        return;
      }
      const a = body as AnaliseResp;
      setAnalise(a);
      // PNG → cadeado fechado por padrão; PDF/TIFF → cadeado aberto.
      setCadeadoFechado(a.cadeado === "fechado");
    } finally {
      setCarregando(false);
    }
  }

  function quandoLarguraMuda(novaLargura: string) {
    setLargura(novaLargura);
    if (!cadeadoFechado || !analise?.proporcao) return;
    const w = Number(novaLargura);
    const p = Number(analise.proporcao);
    if (Number.isFinite(w) && Number.isFinite(p) && p > 0) {
      setAltura(arredondarMm(w / p).toString());
    }
  }

  function quandoAlturaMuda(novaAltura: string) {
    setAltura(novaAltura);
    if (!cadeadoFechado || !analise?.proporcao) return;
    const h = Number(novaAltura);
    const p = Number(analise.proporcao);
    if (Number.isFinite(h) && Number.isFinite(p) && p > 0) {
      setLargura(arredondarMm(h * p).toString());
    }
  }

  async function salvar() {
    if (!arquivo) return;
    setErro(null);
    if (!largura.trim() || !altura.trim()) {
      setErro("Largura e altura são obrigatórias.");
      return;
    }
    const qtd = Number(quantidade);
    if (!Number.isInteger(qtd) || qtd <= 0) {
      setErro("A quantidade de peças com esta arte precisa ser um inteiro ≥ 1.");
      return;
    }
    setCarregando(true);
    try {
      const fd = new FormData();
      fd.append("arquivo", arquivo);
      fd.append("largura_cm", largura.trim());
      fd.append("altura_cm", altura.trim());
      fd.append("quantidade", String(qtd));
      if (observacoes.trim()) fd.append("observacoes", observacoes.trim());
      const res = await fetch(`${API}/pedidos/${pedidoId}/artes`, {
        method: "POST",
        body: fd,
        credentials: "include",
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        const msg =
          (body as ApiErrorBody | null)?.error?.message ?? "Erro ao salvar arte.";
        setErro(msg);
        return;
      }
      reset();
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  async function excluir(arteId: number) {
    setErro(null);
    const res = await fetch(`${API}/pedidos/${pedidoId}/artes/${arteId}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as ApiErrorBody | null;
      setErro(body?.error?.message ?? "Erro ao excluir arte.");
      return;
    }
    router.refresh();
  }

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Artes</h2>

      {artes.length === 0 ? (
        <p className="text-sm text-neutral-500">Nenhuma arte anexada ainda.</p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {artes.map((a) => (
            <li
              key={a.id}
              className="flex items-start gap-3 rounded border border-neutral-200 bg-white p-3"
            >
              {a.arquivo_mime === "image/png" ? (
                <img
                  src={`${API}/pedidos/${pedidoId}/artes/${a.id}/arquivo`}
                  alt={`Arte ${a.ordem}`}
                  className="h-20 w-20 rounded border border-neutral-200 object-contain bg-neutral-50"
                />
              ) : (
                <div className="flex h-20 w-20 items-center justify-center rounded border border-neutral-200 bg-neutral-50 text-xs uppercase text-neutral-500">
                  {a.arquivo_mime.split("/")[1]}
                </div>
              )}
              <div className="flex-1 text-sm">
                <div className="font-medium">
                  #{a.ordem} — {a.largura_cm} × {a.altura_cm} cm
                </div>
                <div className="text-xs text-neutral-600">
                  {a.quantidade} {a.quantidade === 1 ? "peça" : "peças"}
                </div>
                {a.observacoes && (
                  <div className="text-xs text-neutral-600">{a.observacoes}</div>
                )}
                <div className="mt-2 flex gap-2">
                  <a
                    href={`${API}/pedidos/${pedidoId}/artes/${a.id}/arquivo`}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-100"
                  >
                    Abrir
                  </a>
                  <button
                    type="button"
                    onClick={() => excluir(a.id)}
                    className="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                  >
                    Excluir
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="space-y-3 rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-4">
        <div className="text-sm font-medium">Anexar nova arte</div>
        <input
          type="file"
          accept="image/png,application/pdf,image/tiff"
          onChange={(e) => aoEscolherArquivo(e.target.files?.[0] ?? null)}
          className="block w-full text-sm"
        />

        {analise && (
          <div className="text-xs text-neutral-600">
            Formato: <span className="font-mono">{analise.mime}</span>
            {analise.proporcao && (
              <>
                {" · "}Proporção lida:{" "}
                <span className="font-mono">
                  {Number(analise.proporcao).toFixed(4)}
                </span>
              </>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-end gap-2">
          <label className="block">
            <span className="text-xs text-neutral-700">Largura (cm)</span>
            <input
              type="number"
              step="0.1"
              min="0.1"
              value={largura}
              onChange={(e) => quandoLarguraMuda(e.target.value)}
              disabled={!arquivo}
              className="mt-1 block w-28 rounded border border-neutral-300 px-2 py-1 text-sm disabled:bg-neutral-100"
            />
          </label>
          <button
            type="button"
            onClick={() => setCadeadoFechado((v) => !v)}
            disabled={!analise?.proporcao}
            title={
              analise?.proporcao
                ? cadeadoFechado
                  ? "Cadeado fechado — proporção travada"
                  : "Cadeado aberto — largura e altura livres"
                : "Cadeado inativo (só PNG)"
            }
            className="mb-1 rounded border border-neutral-300 px-2 py-1 text-xs hover:bg-neutral-100 disabled:opacity-50"
          >
            {cadeadoFechado ? "🔒" : "🔓"}
          </button>
          <label className="block">
            <span className="text-xs text-neutral-700">Altura (cm)</span>
            <input
              type="number"
              step="0.1"
              min="0.1"
              value={altura}
              onChange={(e) => quandoAlturaMuda(e.target.value)}
              disabled={!arquivo}
              className="mt-1 block w-28 rounded border border-neutral-300 px-2 py-1 text-sm disabled:bg-neutral-100"
            />
          </label>
        </div>

        <label className="block">
          <span className="text-xs text-neutral-700">
            Quantidade de peças com esta arte
          </span>
          <input
            type="number"
            step="1"
            min="1"
            value={quantidade}
            onChange={(e) => setQuantidade(e.target.value)}
            disabled={!arquivo}
            className="mt-1 block w-28 rounded border border-neutral-300 px-2 py-1 text-sm disabled:bg-neutral-100"
          />
          <span className="mt-1 block text-[11px] text-neutral-500">
            Se o pedido tem 3 peças e 2 levam esta estampa, use 2.
          </span>
        </label>

        <label className="block">
          <span className="text-xs text-neutral-700">Observações</span>
          <input
            type="text"
            value={observacoes}
            onChange={(e) => setObservacoes(e.target.value)}
            disabled={!arquivo}
            className="mt-1 block w-full rounded border border-neutral-300 px-2 py-1 text-sm disabled:bg-neutral-100"
          />
        </label>

        <div className="flex gap-2">
          <button
            type="button"
            disabled={!arquivo || carregando}
            onClick={salvar}
            className="rounded bg-neutral-900 px-3 py-1.5 text-sm text-white hover:bg-neutral-800 disabled:opacity-50"
          >
            {carregando ? "Salvando…" : "Adicionar arte"}
          </button>
          {arquivo && (
            <button
              type="button"
              onClick={reset}
              disabled={carregando}
              className="rounded border border-neutral-300 px-3 py-1.5 text-sm hover:bg-neutral-100"
            >
              Limpar
            </button>
          )}
        </div>

        {erro && (
          <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {erro}
          </div>
        )}
      </div>
    </section>
  );
}
