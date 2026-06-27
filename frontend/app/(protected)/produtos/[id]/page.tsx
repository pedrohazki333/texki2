import Link from "next/link";
import { notFound } from "next/navigation";

import { CalculadoraPreco } from "@/components/produtos/calculadora-preco";
import { ConfirmarExclusaoProduto } from "@/components/produtos/confirmar-exclusao-produto";
import { FaixasTabela } from "@/components/produtos/faixas-tabela";
import { NomeProdutoEditavel } from "@/components/produtos/nome-produto-editavel";
import { VariacoesTabela } from "@/components/produtos/variacoes-tabela";
import { apiServerFetch } from "@/lib/api-server";
import type { ProdutoDetalhes } from "@/lib/tipos";

export const dynamic = "force-dynamic";

const LABEL_TIPO: Record<string, string> = {
  dtf_por_metro: "DTF por metro",
  vestuario: "Vestuário",
};

export default async function ProdutoDetalhesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const res = await apiServerFetch(`/produtos/${id}`);
  if (res.status === 404) notFound();
  if (!res.ok) {
    return (
      <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Erro ao carregar produto.
      </div>
    );
  }
  const produto = (await res.json()) as ProdutoDetalhes;

  return (
    <div className="space-y-6">
      <div className="text-sm text-neutral-500">
        <Link href="/produtos" className="hover:underline">
          Produtos
        </Link>{" "}
        / {produto.nome}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <NomeProdutoEditavel id={produto.id} nomeAtual={produto.nome} />
          <p className="text-sm text-neutral-600">
            Tipo:{" "}
            <span className="font-medium">
              {LABEL_TIPO[produto.tipo] ?? produto.tipo}
            </span>{" "}
            <span className="text-xs text-neutral-400">(imutável)</span>
          </p>
        </div>
        <ConfirmarExclusaoProduto produtoId={produto.id} nome={produto.nome} />
      </div>

      {produto.tipo === "vestuario" && (
        <VariacoesTabela
          produtoId={produto.id}
          variacoes={produto.variacoes}
        />
      )}

      <FaixasTabela
        produtoId={produto.id}
        produtoTipo={produto.tipo}
        faixas={produto.faixas}
      />

      <CalculadoraPreco produtoId={produto.id} />
    </div>
  );
}
