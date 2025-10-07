from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def transform(
    value: Any,
    input_format: str = "%Y-%m-%d",
    output_format: str = "%d/%m/%Y",
    **params,
) -> str:
    """Format date string."""
    if not value:
        return ""

    date_obj = datetime.strptime(str(value), input_format).replace(
        tzinfo=ZoneInfo("UTC"),
    )
    return date_obj.strftime(output_format)
