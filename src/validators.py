from datetime import datetime
from fastapi import HTTPException


def validate_month(month: str) -> str:
    """
    Validate the month format (YYYY-MM).
    """
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "value_error",
                    "loc": ["query", "month"],
                    "msg": "Invalid month.",
                }
            ],
        )
    return month
