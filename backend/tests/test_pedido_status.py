"""Troca manual de status do pedido + auditoria (Fatia 4 — RF6, RNF3)."""
from datetime import date, timedelta

from sqlalchemy import select

from app.models.auditoria import Auditoria
from app.models.cliente import Cliente
from app.models.pedido import Pedido


TELEFONE = "(11) 90000-0002"


def _cli(db_session) -> Cliente:
    c = Cliente(
        primeiro_nome="Status",
        telefone=TELEFONE,
        consentimento_lgpd=False,
    )
    db_session.add(c)
    db_session.flush()
    return c


def _pedido(db_session, vendedora, status="recebido") -> Pedido:
    p = Pedido(
        cliente_id=_cli(db_session).id,
        vendedora_id=vendedora.id,
        status=status,
        data_entrega=date.today() + timedelta(days=1),
        total=0,
    )
    db_session.add(p)
    db_session.flush()
    return p


def test_vendedora_troca_status_e_audita(
    client, db_session, vendedora, login
):
    cookie = login(vendedora)
    p = _pedido(db_session, vendedora, "recebido")
    db_session.commit()

    r = client.patch(
        f"/api/pedidos/{p.id}/status",
        cookies={"texki_session": cookie},
        json={"status": "pago"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pago"

    # Linha de auditoria com campo='status', anterior='recebido', novo='pago'.
    audit = db_session.scalars(
        select(Auditoria)
        .where(Auditoria.entidade == "pedido", Auditoria.entidade_id == p.id)
        .order_by(Auditoria.id.desc())
    ).first()
    assert audit is not None
    assert audit.campo == "status"
    assert audit.valor_anterior == "recebido"
    assert audit.valor_novo == "pago"


def test_impressor_pode_trocar_status(client, db_session, vendedora, impressor, login):
    """Impressor também troca status pelo dashboard (Fatia 4), embora não
    seja dono do CRUD (Fatia 3)."""
    p = _pedido(db_session, vendedora, "pago")
    db_session.commit()
    cookie = login(impressor)
    r = client.patch(
        f"/api/pedidos/{p.id}/status",
        cookies={"texki_session": cookie},
        json={"status": "na_fila_de_impressao"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "na_fila_de_impressao"


def test_trocar_status_sem_auth_eh_401(client, db_session, vendedora):
    p = _pedido(db_session, vendedora)
    db_session.commit()
    r = client.patch(f"/api/pedidos/{p.id}/status", json={"status": "pago"})
    assert r.status_code == 401


def test_troca_para_mesmo_status_eh_idempotente(
    client, db_session, vendedora, login
):
    """Sem-op: status já é 'recebido'; não deve gravar nova linha de auditoria
    nem alterar updated_at."""
    cookie = login(vendedora)
    p = _pedido(db_session, vendedora, "recebido")
    db_session.commit()

    antes = db_session.scalar(
        select(Auditoria).where(
            Auditoria.entidade == "pedido", Auditoria.entidade_id == p.id
        )
    )
    assert antes is None

    r = client.patch(
        f"/api/pedidos/{p.id}/status",
        cookies={"texki_session": cookie},
        json={"status": "recebido"},
    )
    assert r.status_code == 200

    # Continua sem linha de auditoria — chamada no-op.
    depois = db_session.scalar(
        select(Auditoria).where(
            Auditoria.entidade == "pedido", Auditoria.entidade_id == p.id
        )
    )
    assert depois is None


def test_status_invalido_eh_rejeitado(client, db_session, vendedora, login):
    """Pydantic valida no schema antes mesmo do service."""
    cookie = login(vendedora)
    p = _pedido(db_session, vendedora)
    db_session.commit()

    r = client.patch(
        f"/api/pedidos/{p.id}/status",
        cookies={"texki_session": cookie},
        json={"status": "fantasma"},
    )
    assert r.status_code in (422, 400)


def test_listar_auditoria_do_pedido(client, db_session, vendedora, login):
    """Smoke: a troca grava em auditoria e o endpoint devolve a linha."""
    cookie = login(vendedora)
    p = _pedido(db_session, vendedora, "recebido")
    db_session.commit()

    client.patch(
        f"/api/pedidos/{p.id}/status",
        cookies={"texki_session": cookie},
        json={"status": "pago"},
    )
    r = client.get(
        f"/api/pedidos/{p.id}/auditoria", cookies={"texki_session": cookie}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert any(
        x["campo"] == "status"
        and x["valor_anterior"] == "recebido"
        and x["valor_novo"] == "pago"
        for x in body
    )
