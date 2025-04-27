from pydantic import BaseModel, Field
from datetime import date


class PriceResponseItem(BaseModel):
    hotel: int
    price: float
    currency: str = Field(..., pattern=r"^[A-Z]{3}$")
    difference: float
    arrival_date: date


class PriceResponse(BaseModel):
    prices: list[PriceResponseItem]
