from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.faixa_preco import FaixaPreco
from app.models.produto import Produto
from app.models.variacao import Variacao
from app.schemas.faixa_preco import FaixaPrecoIn, FaixaPrecoOut, PrecoSelecionadoOut
from app.schemas.produto import ProdutoDetalhesOut, ProdutoIn, ProdutoOut, ProdutoUpdate
from app.schemas.variacao import VariacaoIn, VariacaoOut
from app.services import faixas as faixas_svc
from app.services import produtos as produtos_svc
from app.services import variacoes as variacoes_svc

router = APIRouter(
    dependencies=[Depends(require_role("vendedora", "administrador"))]
)


def _produto_nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "produto.not_found", "message": "Produto não encontrado."},
    )


def _variacao_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "variacao.not_found", "message": "Variação não encontrada."},
    )


def _faixa_nao_encontrada() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "faixa.not_found", "message": "Faixa não encontrada."},
    )


def _obter_produto_ou_404(db: Session, produto_id: int) -> Produto:
    produto = produtos_svc.obter(db, produto_id)
    if produto is None:
        raise _produto_nao_encontrado()
    return produto


def _obter_variacao_do_produto(db: Session, produto_id: int, variacao_id: int) -> Variacao:
    v = variacoes_svc.obter(db, variacao_id)
    if v is None or v.produto_id != produto_id:
        raise _variacao_nao_encontrada()
    return v


def _obter_faixa_do_produto(db: Session, produto_id: int, faixa_id: int) -> FaixaPreco:
    f = faixas_svc.obter(db, faixa_id)
    if f is None or f.produto_id != produto_id:
        raise _faixa_nao_encontrada()
    return f


# ---------- produtos ----------

@router.get("", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db)):
    return [ProdutoOut.model_validate(p) for p in produtos_svc.listar(db)]


@router.post("", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(payload: ProdutoIn, db: Session = Depends(get_db)):
    return ProdutoOut.model_validate(produtos_svc.criar(db, payload))


@router.get("/{produto_id}", response_model=ProdutoDetalhesOut)
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = _obter_produto_ou_404(db, produto_id)
    return ProdutoDetalhesOut.model_validate(produto)


@router.put("/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db)
):
    produto = _obter_produto_ou_404(db, produto_id)
    return ProdutoOut.model_validate(produtos_svc.atualizar_nome(db, produto, payload))


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = _obter_produto_ou_404(db, produto_id)
    produtos_svc.excluir(db, produto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- variações ----------

@router.post(
    "/{produto_id}/variacoes",
    response_model=VariacaoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_variacao(
    produto_id: int, payload: VariacaoIn, db: Session = Depends(get_db)
):
    produto = _obter_produto_ou_404(db, produto_id)
    return VariacaoOut.model_validate(variacoes_svc.criar(db, produto, payload))


@router.put(
    "/{produto_id}/variacoes/{variacao_id}",
    response_model=VariacaoOut,
)
def atualizar_variacao(
    produto_id: int,
    variacao_id: int,
    payload: VariacaoIn,
    db: Session = Depends(get_db),
):
    _obter_produto_ou_404(db, produto_id)
    variacao = _obter_variacao_do_produto(db, produto_id, variacao_id)
    return VariacaoOut.model_validate(variacoes_svc.atualizar(db, variacao, payload))


@router.delete(
    "/{produto_id}/variacoes/{variacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_variacao(
    produto_id: int, variacao_id: int, db: Session = Depends(get_db)
):
    _obter_produto_ou_404(db, produto_id)
    variacao = _obter_variacao_do_produto(db, produto_id, variacao_id)
    variacoes_svc.excluir(db, variacao)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- faixas ----------

@router.post(
    "/{produto_id}/faixas",
    response_model=FaixaPrecoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_faixa(
    produto_id: int, payload: FaixaPrecoIn, db: Session = Depends(get_db)
):
    produto = _obter_produto_ou_404(db, produto_id)
    return FaixaPrecoOut.model_validate(faixas_svc.criar(db, produto, payload))


@router.put(
    "/{produto_id}/faixas/{faixa_id}",
    response_model=FaixaPrecoOut,
)
def atualizar_faixa(
    produto_id: int,
    faixa_id: int,
    payload: FaixaPrecoIn,
    db: Session = Depends(get_db),
):
    produto = _obter_produto_ou_404(db, produto_id)
    faixa = _obter_faixa_do_produto(db, produto_id, faixa_id)
    return FaixaPrecoOut.model_validate(
        faixas_svc.atualizar(db, produto, faixa, payload)
    )


@router.delete(
    "/{produto_id}/faixas/{faixa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_faixa(produto_id: int, faixa_id: int, db: Session = Depends(get_db)):
    _obter_produto_ou_404(db, produto_id)
    faixa = _obter_faixa_do_produto(db, produto_id, faixa_id)
    faixas_svc.excluir(db, faixa)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- consulta de preço ----------

@router.get("/{produto_id}/preco", response_model=PrecoSelecionadoOut)
def consultar_preco(
    produto_id: int,
    medida: Decimal = Query(gt=0),
    db: Session = Depends(get_db),
):
    _obter_produto_ou_404(db, produto_id)
    faixa = faixas_svc.selecionar_por_medida(db, produto_id, medida)
    return PrecoSelecionadoOut(faixa_id=faixa.id, preco_unitario=faixa.preco_unitario)
