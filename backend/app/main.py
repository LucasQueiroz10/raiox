from fastapi import FastAPI

from app.api import raiox, saude
from app.api.erros import registrar_erros

app = FastAPI(title="Projeto RX")
registrar_erros(app)
app.include_router(saude.router)
app.include_router(raiox.router)
