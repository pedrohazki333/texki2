from fastapi import FastAPI

from app.api import auth, clientes, pedidos, produtos
from app.schemas.common import registrar_handlers_de_erro

app = FastAPI(title="TEXKI2 API", version="0.1.0")

registrar_handlers_de_erro(app)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["clientes"])
app.include_router(produtos.router, prefix="/api/produtos", tags=["produtos"])
app.include_router(pedidos.router, prefix="/api/pedidos", tags=["pedidos"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
