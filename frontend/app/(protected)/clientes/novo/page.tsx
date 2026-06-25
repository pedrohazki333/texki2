import Link from "next/link";

import { ClienteForm } from "@/components/clientes/cliente-form";

export default function NovoClientePage() {
  return (
    <div className="space-y-4">
      <div className="text-sm text-neutral-500">
        <Link href="/clientes" className="hover:underline">
          Clientes
        </Link>{" "}
        / Novo
      </div>
      <h1 className="text-2xl font-semibold">Novo cliente</h1>
      <ClienteForm modo="criar" />
    </div>
  );
}
