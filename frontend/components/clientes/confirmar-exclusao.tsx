"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";

type Props = {
  clienteId: number;
  nomeCompleto: string;
};

type Estado =
  | { tipo: "inicial" }
  | { tipo: "bloqueado_por_pedidos"; mensagem: string }
  | { tipo: "erro"; mensagem: string };

export function ConfirmarExclusao({ clienteId, nomeCompleto }: Props) {
  const router = useRouter();
  const [aberto, setAberto] = useState(false);
  const [carregando, setCarregando] = useState(false);
  const [estado, setEstado] = useState<Estado>({ tipo: "inicial" });

  function abrir() {
    setEstado({ tipo: "inicial" });
    setAberto(true);
  }

  async function excluir() {
    setCarregando(true);
    try {
      const res = await apiClientFetch<void>(`/clientes/${clienteId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        if (res.error.code === "cliente.tem_pedidos") {
          setEstado({ tipo: "bloqueado_por_pedidos", mensagem: res.error.message });
        } else {
          setEstado({ tipo: "erro", mensagem: res.error.message });
        }
        return;
      }
      setAberto(false);
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  async function anonimizar() {
    setCarregando(true);
    try {
      const res = await apiClientFetch(`/clientes/${clienteId}/anonimizar`, {
        method: "POST",
      });
      if (!res.ok) {
        setEstado({ tipo: "erro", mensagem: res.error.message });
        return;
      }
      setAberto(false);
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={abrir}
        className="rounded border border-red-300 px-3 py-1 text-xs text-red-700 hover:bg-red-50"
      >
        Excluir
      </button>

      {aberto && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4"
        >
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Excluir cliente</h2>

            {estado.tipo === "bloqueado_por_pedidos" ? (
              <>
                <p className="mt-2 text-sm text-neutral-700">
                  <strong>{nomeCompleto}</strong> tem pedidos vinculados, então não
                  pode ser excluído. Para o direito de esquecimento (LGPD), os
                  dados pessoais podem ser <strong>anonimizados</strong>: nome,
                  telefone e endereço são apagados, mas os pedidos permanecem.
                </p>
                <div className="mt-3 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                  {estado.mensagem}
                </div>
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
                    onClick={anonimizar}
                    disabled={carregando}
                    className="rounded bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-700 disabled:opacity-50"
                  >
                    {carregando ? "Anonimizando…" : "Anonimizar"}
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="mt-2 text-sm text-neutral-700">
                  Excluir cliente <strong>{nomeCompleto}</strong>? Esta ação não
                  pode ser desfeita.
                </p>
                {estado.tipo === "erro" && (
                  <div className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {estado.mensagem}
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
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
