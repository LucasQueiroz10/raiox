from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Saude(BaseModel):
    status: Literal["ok"]


@router.get("/saude")
def saude() -> Saude:
    return Saude(status="ok")
