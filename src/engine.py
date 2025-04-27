import json
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from src.enums import Currency
from src.database import get_db
from src.schemas import PriceResponseItem
from sqlalchemy.sql import text
from loguru import logger


class Engine:

    def __init__(self):
        pass

    async def find_prices(
        self, hotels: list[int], month: str, cancellable: bool
    ) -> pd.DataFrame:
        timestamp = datetime.now()
        async for db in get_db():

            # Fetch from the database
            conditions = " OR ".join(
                [f"key LIKE '{hotel}_{month}-%_{month}-%'" for hotel in hotels]
            )
            query = text(f"SELECT key, value FROM prices WHERE {conditions};")
            cursor = await db.execute(query)
            rows = cursor.fetchall()

            # Unpack the rows
            rows = [json.loads(row[1]) for row in rows]
            result = pd.DataFrame(rows).explode("prices")

            # Get latest updated prices
            result = result.sort_values(
                "extract_date", ascending=False
            ).drop_duplicates(["arrival_date", "our_hotel_id"])

            # Transform epoch to date
            result["arrival_date"] = result["arrival_date"].apply(self.epoch_to_date)
            result["extract_date"] = result["extract_date"].apply(self.epoch_to_date)

            # Filter by cancellable
            result = result[
                result["prices"].apply(lambda x: x["is_cancellable"] is cancellable)
            ]

            # Extract price and currency
            result["price"] = result["prices"].apply(lambda x: x["price_value"])
            result["currency"] = result["prices"].apply(lambda x: x["currency"])

            # Clean up the DataFrame
            result = result.rename(columns={"our_hotel_id": "hotel_id"})
            result = result[
                ["hotel_id", "arrival_date", "extract_date", "price", "currency"]
            ]

            # Prepare key for merging and sort
            result["day"] = result["arrival_date"].apply(self.remove_month_from_date)
            result = result.sort_values(["hotel_id", "arrival_date"])
            logger.debug(
                f"Prices fetched in {(datetime.now() - timestamp).microseconds} μs"
            )
            return result

        return pd.DataFrame()

    @staticmethod
    def epoch_to_date(epoch: int) -> str:
        return datetime.fromtimestamp(epoch * 86400).strftime("%Y-%m-%d")

    @staticmethod
    def remove_month_from_date(date: str) -> str:
        return date.split("-", maxsplit=1)[1]

    @staticmethod
    async def find_exchange_rate(currency: Currency, month: str) -> pd.DataFrame:
        timestamp = datetime.now()
        async for db in get_db():
            query = text(
                "SELECT * FROM rates WHERE currency = :currency AND extract_date LIKE :month"
            )
            cursor = await db.execute(
                query, {"currency": currency, "month": f"{month}%"}
            )
            logger.debug(
                f"Exchange rates fetched in {(datetime.now() - timestamp).microseconds} μs"
            )
            return pd.DataFrame(
                cursor.fetchall(), columns=["currency", "rate", "extract_date"]
            )
        return pd.DataFrame()

    @staticmethod
    async def get_month_in_past(month: str, years_ago: int) -> str:
        month_in_past = datetime.strptime(f"{month}-01", "%Y-%m-%d") - timedelta(
            days=years_ago * 365
        )
        return month_in_past.strftime("%Y-%m")

    async def find_hotel_prices(
        self,
        month: str,
        hotels: list[int],
        currency: Currency,
        years_ago: int,
        cancellable: bool,
    ):
        # Get the month in the past
        month_in_past = await self.get_month_in_past(month=month, years_ago=years_ago)

        # Fetch prices and exchange rates concurrently
        timestamp = datetime.now()
        past_prices, current_prices, past_rates, current_rates = await asyncio.gather(
            self.find_prices(
                hotels=hotels, month=month_in_past, cancellable=cancellable
            ),
            self.find_prices(hotels=hotels, month=month, cancellable=cancellable),
            self.find_exchange_rate(currency=currency, month=month_in_past),
            self.find_exchange_rate(currency=currency, month=month),
        )
        logger.debug(
            f"All data fetched in {(datetime.now() - timestamp).microseconds} μs"
        )

        # Aggregate data
        timestamp = datetime.now()
        current_prices = current_prices.merge(
            current_rates, on="extract_date", how="left", suffixes=("", "_target")
        )
        past_prices = past_prices.merge(
            past_rates, on="extract_date", how="left", suffixes=("", "_target")
        )
        prices = current_prices.merge(
            past_prices, on=["hotel_id", "day"], how="left", suffixes=("", "_past")
        )

        # Calculate fields
        prices["price_converted"] = (prices["price"] * prices["rate"]).round(2)
        prices["price_converted_past"] = (
            prices["price_past"] * prices["rate_past"]
        ).round(2)
        prices["difference"] = (
            prices["price_converted"] - prices["price_converted_past"]
        ).round(2)
        logger.debug(
            f"Data aggregated in {(datetime.now() - timestamp).microseconds} μs"
        )

        # Return the response
        return [
            PriceResponseItem(
                hotel=row["hotel_id"],
                price=row["price_converted"],
                currency=row["currency_target"],
                difference=row["difference"],
                arrival_date=row["arrival_date"],
            )
            for row in prices.to_dict(orient="records")
        ]
