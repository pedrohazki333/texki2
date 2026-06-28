"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type {
  Cliente,
  PedidoDetalhes,
  PrecoSelecionado,
  ProdutoDetalhes,
} from "@/lib/tipos";

type ItemForm = {
  uid: string; // chave estável de linha (form-local)
  produto_id: number | "";
  variacao_id: number | "";
  quantidade: string;
  preco_unitario?: string; // preview do backend
  subtotal?: string; // preview calculado localmente
};

type Props =
  | {
      modo: "criar";
      clientes: Cliente[];
      produtos: ProdutoDetalhes[];
      inicial?: undefined;
    }
  | {
      modo: "editar";
      clientes: Cliente[];
      produtos: ProdutoDetalhes[];
      inicial: PedidoDetalhes;
    };

function novoUid(): string {
  return Math.random().toString(36).slice(2, 10);
}

function nomeCliente(c: Cliente): string {
  return c.ultimo_nome ? `${c.primeiro_nome} ${c.ultimo_nome}` : c.primeiro_nome;
}

function calcularSubtotal(qtd: string, preco: string | undefined): string | undefined {
  if (!preco) return undefined;
  const q = Number(qtd);
  const p = Number(preco);
  if (!Number.isFinite(q) || !Number.isFinite(p)) return undefined;
  return (q * p).toFixed(2);
}

export function PedidoForm(props: Props) {
  const { modo, clientes, produtos } = props;
  const inicial = modo === "editar" ? props.inicial : undefined;
  const router = useRouter();

  const [clienteId, setClienteId] = useState<number | "">(inicial?.cliente_id ?? "");
  const [dataEntrega, setDataEntrega] = useState<string>(
    inicial?.data_entrega ?? "",
  );
  const [itens, setItens] = useState<ItemForm[]>(
    inicial?.itens.map((i) => ({
      uid: novoUid(),
      produto_id: i.produto_id,
      variacao_id: i.variacao_id ?? "",
      quantidade: i.quantidade,
      preco_unitario: i.preco_unitario,
      subtotal: i.subtotal,
    })) ?? [
      {
        uid: novoUid(),
        produto_id: "",
        variacao_id: "",
        quantidade: "",
      },
    ],
  );
  const [erroGeral, setErroGeral] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const totalPreview = useMemo(() => {
    let acc = 0;
    for (const it of itens) {
      const s = Number(it.subtotal);
      if (Number.isFinite(s)) acc += s;
    }
    return acc.toFixed(2);
  }, [itens]);

  function atualizarItem(uid: string, patch: Partial<ItemForm>) {
    setItens((arr) =>
      arr.map((it) => (it.uid === uid ? { ...it, ...patch } : it)),
    );
  }

  function adicionarLinha() {
    setItens((arr) => [
      ...arr,
      { uid: novoUid(), produto_id: "", variacao_id: "", quantidade: "" },
    ]);
  }

  function removerLinha(uid: string) {
    setItens((arr) => (arr.length <= 1 ? arr : arr.filter((it) => it.uid !== uid)));
  }

  async function calcularPrecoDoItem(uid: string) {
    const item = itens.find((i) => i.uid === uid);
    if (!item || item.produto_id === "" || !item.quantidade.trim()) return;
    const res = await apiClientFetch<PrecoSelecionado>(
      `/produtos/${item.produto_id}/preco?medida=${encodeURIComponent(item.quantidade.trim())}`,
    );
    if (!res.ok) {
      atualizarItem(uid, { preco_unitario: undefined, subtotal: undefined });
      return;
    }
    atualizarItem(uid, {
      preco_unitario: res.data.preco_unitario,
      subtotal: calcularSubtotal(item.quantidade, res.data.preco_unitario),
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErroGeral(null);
    if (clienteId === "" || !dataEntrega) {
      setErroGeral("Cliente e data de entrega são obrigatórios.");
      return;
    }
    if (itens.length === 0 || itens.some((i) => i.produto_id === "" || !i.quantidade.trim())) {
      setErroGeral("Adicione ao menos 1 item com produto e quantidade.");
      return;
    }

    setCarregando(true);
    try {
      const payload = {
        cliente_id: clienteId,
        data_entrega: dataEntrega,
        itens: itens.map((i) => ({
          produto_id: i.produto_id,
          variacao_id: i.variacao_id === "" ? null : i.variacao_id,
          quantidade: i.quantidade.trim(),
        })),
      };

      const res =
        modo === "criar"
          ? await apiClientFetch<PedidoDetalhes>("/pedidos", {
              method: "POST",
              body: JSON.stringify(payload),
            })
          : await apiClientFetch<PedidoDetalhes>(`/pedidos/${props.inicial.id}`, {
              method: "PUT",
              body: JSON.stringify(payload),
            });

      if (!res.ok) {
        setErroGeral(res.error.message);
        return;
      }
      if (modo === "criar") {
        router.push(`/pedidos/${res.data.id}`);
      } else {
        router.refresh();
      }
    } finally {
      setCarregando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="block">
          <span className="text-sm text-neutral-700">
            Cliente <span className="text-red-600">*</span>
          </span>
          <select
            value={clienteId}
            onChange={(e) =>
              setClienteId(e.target.value === "" ? "" : Number(e.target.value))
            }
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
          >
            <option value="">Selecione…</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {nomeCliente(c)} · {c.telefone}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm text-neutral-700">
            Data de entrega <span className="text-red-600">*</span>
          </span>
          <input
            type="date"
            value={dataEntrega}
            onChange={(e) => setDataEntrega(e.target.value)}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
          />
        </label>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Itens</h2>
          <button
            type="button"
            onClick={adicionarLinha}
            className="rounded border border-neutral-300 px-3 py-1 text-sm hover:bg-neutral-100"
          >
            Adicionar item
          </button>
        </div>

        <div className="space-y-2">
          {itens.map((it) => {
            const produto = produtos.find((p) => p.id === it.produto_id);
            const precisaVariacao = produto?.tipo === "vestuario";
            return (
              <div
                key={it.uid}
                className="grid grid-cols-1 items-end gap-2 rounded border border-neutral-200 bg-white p-3 md:grid-cols-[2fr_1.5fr_1fr_1fr_1fr_auto]"
              >
                <label className="block">
                  <span className="text-xs text-neutral-700">Produto</span>
                  <select
                    value={it.produto_id}
                    onChange={(e) => {
                      const novoId = e.target.value === "" ? "" : Number(e.target.value);
                      atualizarItem(it.uid, {
                        produto_id: novoId,
                        variacao_id: "",
                        preco_unitario: undefined,
                        subtotal: undefined,
                      });
                    }}
                    className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm"
                  >
                    <option value="">Selecione…</option>
                    {produtos.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.nome} ({p.tipo === "vestuario" ? "vest." : "DTF/m"})
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-xs text-neutral-700">
                    Variação{precisaVariacao && <span className="text-red-600"> *</span>}
                  </span>
                  <select
                    disabled={!precisaVariacao}
                    value={it.variacao_id}
                    onChange={(e) =>
                      atualizarItem(it.uid, {
                        variacao_id:
                          e.target.value === "" ? "" : Number(e.target.value),
                      })
                    }
                    className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm disabled:bg-neutral-100"
                  >
                    <option value="">
                      {precisaVariacao ? "Selecione…" : "— (não se aplica)"}
                    </option>
                    {(produto?.variacoes ?? []).map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.cor} · {v.tamanho}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-xs text-neutral-700">
                    {produto?.tipo === "dtf_por_metro" ? "Metros" : "Quantidade"}
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={it.quantidade}
                    onChange={(e) =>
                      atualizarItem(it.uid, {
                        quantidade: e.target.value,
                        preco_unitario: undefined,
                        subtotal: undefined,
                      })
                    }
                    onBlur={() => calcularPrecoDoItem(it.uid)}
                    className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm"
                  />
                </label>

                <div className="text-sm">
                  <div className="text-xs text-neutral-500">Preço unit.</div>
                  <div className="mt-1">
                    {it.preco_unitario ? `R$ ${it.preco_unitario}` : "—"}
                  </div>
                </div>

                <div className="text-sm">
                  <div className="text-xs text-neutral-500">Subtotal</div>
                  <div className="mt-1 font-medium">
                    {it.subtotal ? `R$ ${it.subtotal}` : "—"}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => removerLinha(it.uid)}
                  disabled={itens.length === 1}
                  className="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50 disabled:opacity-40"
                >
                  Remover
                </button>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end text-sm text-neutral-700">
          <div>
            Total previsto:{" "}
            <span className="font-semibold">R$ {totalPreview}</span>{" "}
            <span className="text-xs text-neutral-500">
              (calculado de novo no servidor)
            </span>
          </div>
        </div>
      </section>

      {erroGeral && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {erroGeral}
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
          onClick={() => router.push("/pedidos")}
          disabled={carregando}
          className="rounded border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-100"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
