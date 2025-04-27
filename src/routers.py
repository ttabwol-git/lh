from fastapi import Query, Depends, APIRouter, Request

from src.enums import Currency
from src.engine import Engine
from src.schemas import PriceResponse
from loguru import logger

router = APIRouter()


@router.get(
    "/pricing/pre_corona_difference",
    response_model=PriceResponse,
    summary="Pricing difference API.",
)
async def get_price_difference(
    request: Request,
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    currency: Currency = Query(..., pattern=r"^[A-Z]{3}$"),
    hotels: list[int] = Query(..., max_length=10),
    years_ago: int = Query(..., ge=1, le=5),
    cancellable: bool | None = Query(True),
    engine: Engine = Depends(Engine),
):
    logger.info(f"{request.method} - {request.url.path}")
    response = await engine.find_hotel_prices(
        month=month,
        hotels=hotels,
        currency=currency,
        years_ago=years_ago,
        cancellable=cancellable,
    )
    logger.success("Prices fetched successfully")
    return PriceResponse(prices=response)
