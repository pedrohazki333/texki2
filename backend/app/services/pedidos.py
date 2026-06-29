from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.cliente import Cliente
from app.models.item_pedido import ItemPedido
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.models.variacao import Variacao
from app.schemas.pedido import ItemPedidoIn, PedidoIn, PedidoUpdate
from app.services import auditoria as auditoria_svc
from app.services import faixas as faixas_svc


def _erro(code: str, message: str, http: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> HTTPException:
    return HTTPException(status_code=http, detail={"code": code, "message": message})


def _validar_item(db: Session, item: ItemPedidoIn) -> tuple[Produto, Variacao | None]:
    produto = db.get(Produto, item.produto_id)
    if produto is None:
        raise _erro("pedido.produto_inexistente", "Produto não encontrado.", status.HTTP_422_UNPROCESSABLE_ENTITY)

    variacao: Variacao | None = None
    if produto.tipo == "vestuario":
        if item.variacao_id is None:
            raise _erro(
                "pedido.variacao_obrigatoria",
                f"O produto '{produto.nome}' exige variação (cor/tamanho).",
            )
        variacao = db.get(Variacao, item.variacao_id)
        if variacao is None or variacao.produto_id != produto.id:
            raise _erro(
                "pedido.variacao_invalida",
                "Variação não encontrada ou não pertence ao produto.",
            )
    else:
        if item.variacao_id is not None:
            raise _erro(
                "pedido.variacao_indevida",
                "Produtos do tipo 'DTF por metro' não aceitam variação.",
            )
    return produto, variacao


def _construir_item(db: Session, item_in: ItemPedidoIn) -> ItemPedido:
    produto, variacao = _validar_item(db, item_in)
    # selecionar_por_medida usa a regra min < medida <= max e dispara erro claro
    # se a configuração de faixas tiver lacunas (preco.sem_faixa_para_medida).
    faixa = faixas_svc.selecionar_por_medida(db, produto.id, item_in.quantidade)
    preco_unitario = faixa.preco_unitario
    subtotal = (Decimal(item_in.quantidade) * preco_unitario).quantize(Decimal("0.01"))
    return ItemPedido(
        produto_id=produto.id,
        variacao_id=variacao.id if variacao else None,
        quantidade=item_in.quantidade,
        preco_unitario=preco_unitario,
        subtotal=subtotal,
    )


def _validar_cliente(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise _erro("pedido.cliente_inexistente", "Cliente não encontrado.")
    return cliente


def _total(itens: list[ItemPedido]) -> Decimal:
    return sum((i.subtotal for i in itens), Decimal("0.00")).quantize(Decimal("0.01"))


def listar(db: Session) -> list[Pedido]:
    return list(
        db.scalars(
            select(Pedido)
            .options(selectinload(Pedido.cliente))
            .order_by(Pedido.created_at.desc())
        )
    )


# Status que aparecem no dashboard. Cancelado e entregue ficam fora —
# o pedido fica concluído (ou abortado) e não polui a visão ativa.
# Ambos seguem visíveis na lista completa.
STATUS_DASHBOARD: tuple[str, ...] = (
    "recebido",
    "pago",
    "na_fila_de_impressao",
    "impressao_pronta",
    "pedido_pronto",
)


def listar_por_status(db: Session) -> dict[str, list[Pedido]]:
    """Agrupa pedidos visíveis no dashboard por status; ordena por data dentro
    do grupo. Carrega cliente e artes (ordem) para o card."""
    pedidos = db.scalars(
        select(Pedido)
        .options(
            selectinload(Pedido.cliente),
            selectinload(Pedido.artes),
        )
        .where(Pedido.status.in_(STATUS_DASHBOARD))
        .order_by(Pedido.status, Pedido.created_at.desc())
    )
    agrupado: dict[str, list[Pedido]] = {s: [] for s in STATUS_DASHBOARD}
    for p in pedidos:
        agrupado[p.status].append(p)
    return agrupado


def obter(db: Session, pedido_id: int) -> Pedido | None:
    return db.scalar(
        select(Pedido)
        .options(
            selectinload(Pedido.itens),
            selectinload(Pedido.artes),
            selectinload(Pedido.cliente),
        )
        .where(Pedido.id == pedido_id)
    )


def criar(db: Session, payload: PedidoIn, vendedora: Usuario) -> Pedido:
    _validar_cliente(db, payload.cliente_id)
    itens = [_construir_item(db, item) for item in payload.itens]
    pedido = Pedido(
        cliente_id=payload.cliente_id,
        vendedora_id=vendedora.id,
        status="recebido",
        data_entrega=payload.data_entrega,
        total=_total(itens),
        itens=itens,
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


def atualizar(db: Session, pedido: Pedido, payload: PedidoUpdate) -> Pedido:
    _validar_cliente(db, payload.cliente_id)
    # Recria itens do zero — recalcular preço pela faixa atual com a nova
    # quantidade re-congela o preco_unitario neste momento (regra acordada).
    novos_itens = [_construir_item(db, item) for item in payload.itens]
    pedido.cliente_id = payload.cliente_id
    pedido.data_entrega = payload.data_entrega
    pedido.itens = novos_itens
    pedido.total = _total(novos_itens)
    db.commit()
    db.refresh(pedido)
    return pedido


def excluir(db: Session, pedido: Pedido) -> None:
    db.delete(pedido)
    db.commit()


VALORES_STATUS: tuple[str, ...] = (
    "recebido",
    "pago",
    "na_fila_de_impressao",
    "impressao_pronta",
    "pedido_pronto",
    "entregue",
    "cancelado",
)


def trocar_status(
    db: Session, pedido: Pedido, novo_status: str, ator: Usuario
) -> Pedido:
    """Troca manual de status. Idempotente: se igual ao atual, não audita
    nem commita."""
    if novo_status not in VALORES_STATUS:
        raise _erro(
            "pedido.status_invalido",
            f"Status '{novo_status}' não existe.",
        )
    if novo_status == pedido.status:
        return pedido
    anterior = pedido.status
    pedido.status = novo_status
    auditoria_svc.registrar(
        db,
        usuario_id=ator.id,
        entidade="pedido",
        entidade_id=pedido.id,
        campo="status",
        valor_anterior=anterior,
        valor_novo=novo_status,
    )
    db.commit()
    db.refresh(pedido)
    return pedido


def trocar_responsavel(
    db: Session, pedido: Pedido, nova_vendedora_id: int, ator: Usuario
) -> Pedido:
    if nova_vendedora_id == pedido.vendedora_id:
        return pedido
    nova = db.get(Usuario, nova_vendedora_id)
    if nova is None or nova.role not in ("vendedora", "administrador"):
        raise _erro(
            "pedido.responsavel_invalido",
            "Responsável precisa ser uma vendedora ou administrador ativo.",
        )
    anterior = pedido.vendedora_id
    pedido.vendedora_id = nova_vendedora_id
    auditoria_svc.registrar(
        db,
        usuario_id=ator.id,
        entidade="pedido",
        entidade_id=pedido.id,
        campo="vendedora_id",
        valor_anterior=str(anterior),
        valor_novo=str(nova_vendedora_id),
    )
    db.commit()
    db.refresh(pedido)
    return pedido


def cliente_tem_pedidos(db: Session, cliente_id: int) -> bool:
    return (
        db.scalar(select(Pedido.id).where(Pedido.cliente_id == cliente_id).limit(1))
        is not None
    )


def produto_tem_itens(db: Session, produto_id: int) -> bool:
    return (
        db.scalar(
            select(ItemPedido.id).where(ItemPedido.produto_id == produto_id).limit(1)
        )
        is not None
    )
