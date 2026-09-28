from fastapi import FastAPI

from app.api import raiox, saude

app = FastAPI(title="Projeto RX")
app.include_router(saude.router)
app.include_router(raiox.router)
