from fastapi import FastAPI

from app.api import saude

app = FastAPI(title="Projeto RX")
app.include_router(saude.router)
