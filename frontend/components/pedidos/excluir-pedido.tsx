"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";

type Props = {
  pedidoId: number;
};

export function ExcluirPedido({ pedidoId }: Props) {
  const router = useRouter();
  const [aberto, setAberto] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function excluir() {
    setCarregando(true);
    setErro(null);
    try {
      const res = await apiClientFetch<void>(`/pedidos/${pedidoId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        setErro(res.error.message);
        return;
      }
      router.push("/pedidos");
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="rounded border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50"
      >
        Excluir pedido
      </button>

      {aberto && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4"
        >
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Excluir pedido</h2>
            <p className="mt-2 text-sm text-neutral-700">
              Excluir o pedido #{pedidoId}? Esta ação não pode ser desfeita.
            </p>
            {erro && (
              <div className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {erro}
              </div>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setAberto(false)}
                disabled={carregando}
                className="rounded border border-neutral-300 px-3 py-1 text-sm hover:bg-neutral-100"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={excluir}
                disabled={carregando}
                className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50"
              >
                {carregando ? "Excluindo…" : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
