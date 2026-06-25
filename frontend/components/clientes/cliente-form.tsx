"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiClientFetch } from "@/lib/api-client";
import type { Cliente } from "@/lib/tipos";

type Props =
  | { modo: "criar"; inicial?: undefined }
  | { modo: "editar"; inicial: Cliente };

const REGEX_TELEFONE = /^\(\d{2}\) \d{4,5}-\d{4}$/;

type CamposErro = Partial<
  Record<"primeiro_nome" | "ultimo_nome" | "endereco" | "telefone" | "consentimento_lgpd", string>
>;

export function ClienteForm(props: Props) {
  const { modo } = props;
  const inicial = modo === "editar" ? props.inicial : undefined;
  const router = useRouter();

  const [primeiroNome, setPrimeiroNome] = useState(inicial?.primeiro_nome ?? "");
  const [ultimoNome, setUltimoNome] = useState(inicial?.ultimo_nome ?? "");
  const [endereco, setEndereco] = useState(inicial?.endereco ?? "");
  const [telefone, setTelefone] = useState(inicial?.telefone ?? "");
  const [consentimento, setConsentimento] = useState(inicial?.consentimento_lgpd ?? false);

  const [erroGeral, setErroGeral] = useState<string | null>(null);
  const [errosCampo, setErrosCampo] = useState<CamposErro>({});
  const [carregando, setCarregando] = useState(false);

  function validarLocal(): boolean {
    const erros: CamposErro = {};
    if (!primeiroNome.trim()) erros.primeiro_nome = "Obrigatório.";
    const tel = telefone.trim();
    if (!tel) erros.telefone = "Obrigatório.";
    else if (!REGEX_TELEFONE.test(tel))
      erros.telefone = "Formato esperado: (XX) XXXX-XXXX ou (XX) XXXXX-XXXX.";
    setErrosCampo(erros);
    return Object.keys(erros).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErroGeral(null);
    if (!validarLocal()) return;

    setCarregando(true);
    try {
      const payload = {
        primeiro_nome: primeiroNome.trim(),
        ultimo_nome: ultimoNome.trim() || null,
        endereco: endereco.trim() || null,
        telefone: telefone.trim(),
        consentimento_lgpd: consentimento,
      };

      const res =
        modo === "criar"
          ? await apiClientFetch<Cliente>("/clientes", {
              method: "POST",
              body: JSON.stringify(payload),
            })
          : await apiClientFetch<Cliente>(`/clientes/${props.inicial.id}`, {
              method: "PUT",
              body: JSON.stringify(payload),
            });

      if (!res.ok) {
        setErroGeral(res.error.message);
        const novos: CamposErro = {};
        for (const d of res.error.details ?? []) {
          const campo = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : undefined;
          if (typeof campo === "string" && d.msg) {
            novos[campo as keyof CamposErro] = d.msg;
          }
        }
        if (Object.keys(novos).length) setErrosCampo(novos);
        return;
      }

      router.push("/clientes");
      router.refresh();
    } finally {
      setCarregando(false);
    }
  }

  function inputClass(campo: keyof CamposErro) {
    const base =
      "mt-1 w-full rounded border px-3 py-2 focus:outline-none focus:border-neutral-500";
    return errosCampo[campo]
      ? `${base} border-red-400`
      : `${base} border-neutral-300`;
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
      <label className="block">
        <span className="text-sm text-neutral-700">
          Primeiro nome <span className="text-red-600">*</span>
        </span>
        <input
          type="text"
          value={primeiroNome}
          onChange={(e) => setPrimeiroNome(e.target.value)}
          maxLength={120}
          className={inputClass("primeiro_nome")}
        />
        {errosCampo.primeiro_nome && (
          <span className="text-xs text-red-600">{errosCampo.primeiro_nome}</span>
        )}
      </label>

      <label className="block">
        <span className="text-sm text-neutral-700">Último nome</span>
        <input
          type="text"
          value={ultimoNome}
          onChange={(e) => setUltimoNome(e.target.value)}
          maxLength={120}
          className={inputClass("ultimo_nome")}
        />
      </label>

      <label className="block">
        <span className="text-sm text-neutral-700">Endereço</span>
        <input
          type="text"
          value={endereco}
          onChange={(e) => setEndereco(e.target.value)}
          maxLength={255}
          className={inputClass("endereco")}
        />
      </label>

      <label className="block">
        <span className="text-sm text-neutral-700">
          Telefone <span className="text-red-600">*</span>
        </span>
        <input
          type="tel"
          value={telefone}
          onChange={(e) => setTelefone(e.target.value)}
          placeholder="(11) 98765-4321"
          maxLength={40}
          className={inputClass("telefone")}
        />
        {errosCampo.telefone && (
          <span className="text-xs text-red-600">{errosCampo.telefone}</span>
        )}
      </label>

      <label className="flex items-start gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={consentimento}
          onChange={(e) => setConsentimento(e.target.checked)}
          className="mt-1"
        />
        <span className="text-sm text-neutral-700">
          Cliente consentiu o uso de dados conforme a LGPD.
          <br />
          <span className="text-xs text-neutral-500">
            Marcar registra a data de hoje; desmarcar limpa a data.
          </span>
        </span>
      </label>

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
          onClick={() => router.push("/clientes")}
          disabled={carregando}
          className="rounded border border-neutral-300 px-4 py-2 text-sm hover:bg-neutral-100"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
