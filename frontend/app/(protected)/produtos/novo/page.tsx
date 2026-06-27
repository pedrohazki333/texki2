import Link from "next/link";

import { ProdutoForm } from "@/components/produtos/produto-form";

export default function NovoProdutoPage() {
  return (
    <div className="space-y-4">
      <div className="text-sm text-neutral-500">
        <Link href="/produtos" className="hover:underline">
          Produtos
        </Link>{" "}
        / Novo
      </div>
      <h1 className="text-2xl font-semibold">Novo produto</h1>
      <ProdutoForm />
    </div>
  );
}
