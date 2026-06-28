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

export type TipoProduto = "dtf_por_metro" | "vestuario";
export type BaseFaixa = "comprimento_m" | "quantidade";

export type Produto = {
  id: number;
  nome: string;
  tipo: TipoProduto;
};

export type Variacao = {
  id: number;
  cor: string;
  tamanho: string;
};

export type FaixaPreco = {
  id: number;
  base: BaseFaixa;
  min: string;
  max: string | null;
  preco_unitario: string;
};

export type ProdutoDetalhes = Produto & {
  variacoes: Variacao[];
  faixas: FaixaPreco[];
};

export type PrecoSelecionado = {
  faixa_id: number;
  preco_unitario: string;
};

export type PedidoStatus =
  | "recebido"
  | "pago"
  | "na_fila_de_impressao"
  | "impressao_pronta"
  | "pedido_pronto"
  | "entregue"
  | "cancelado";

export type Pedido = {
  id: number;
  cliente_id: number;
  vendedora_id: number;
  status: PedidoStatus;
  data_entrega: string;
  total: string;
  created_at: string;
};

export type ItemPedido = {
  id: number;
  produto_id: number;
  variacao_id: number | null;
  quantidade: string;
  preco_unitario: string;
  subtotal: string;
};

export type Arte = {
  id: number;
  arquivo_mime: string;
  largura_cm: string;
  altura_cm: string;
  observacoes: string | null;
  ordem: number;
};

export type PedidoDetalhes = Pedido & {
  itens: ItemPedido[];
  artes: Arte[];
  cliente: Cliente;
};

export type ResponsavelPossivel = {
  id: number;
  nome: string;
  role: Role;
};

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details: Array<{ loc?: unknown[]; msg?: string; type?: string }>;
  };
};
