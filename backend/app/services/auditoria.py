from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria


def registrar(
    db: Session,
    *,
    usuario_id: int,
    entidade: str,
    entidade_id: int,
    campo: str,
    valor_anterior: str | None,
    valor_novo: str | None,
) -> Auditoria:
    """Cria uma linha de auditoria. Flush, sem commit — quem chama commita."""
    linha = Auditoria(
        usuario_id=usuario_id,
        entidade=entidade,
        entidade_id=entidade_id,
        campo=campo,
        valor_anterior=valor_anterior,
        valor_novo=valor_novo,
    )
    db.add(linha)
    db.flush()
    return linha
