export type Role = "vendedora" | "impressor" | "administrador";

export type UsuarioAtual = {
  id: number;
  email: string;
  nome: string;
  role: Role;
};

export type Cliente = {
  id: number;
  primeiro_nome: string;
  ultimo_nome: string | null;
  endereco: string | null;
  telefone: string;
  consentimento_lgpd: boolean;
  data_consentimento: string | null;
};

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details: Array<{ loc?: unknown[]; msg?: string; type?: string }>;
  };
};
