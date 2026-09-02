from __future__ import annotations

from typing import Dict, List

import requests

from decorators import logger

DEFAULT_CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


@logger
def get_currencies(
    currency_codes: List[str],
    url: str = DEFAULT_CBR_URL,
) -> Dict[str, float]:

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Ошибка при запросе к API: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError(f"Некорректный JSON в ответе API: {exc}") from exc

    if "Valute" not in data:
        raise KeyError("В ответе API отсутствует ключ 'Valute'")

    valute = data["Valute"]
    result: Dict[str, float] = {}

    for code in currency_codes:
        if code not in valute:
            raise KeyError(f"Валюта '{code}' отсутствует в данных API")

        value = valute[code].get("Value")
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Курс валюты '{code}' имеет неверный тип: "
                f"{type(value).__name__}"
            )

        result[code] = float(value)

    return result

import logging

from currencies import get_currencies
from decorators import logger

file_logger = logging.getLogger("currency")
file_logger.setLevel(logging.INFO)

_handler = logging.FileHandler("currency.log", encoding="utf-8")
_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s")
)
file_logger.addHandler(_handler)


@logger(handle=file_logger)
def get_currencies_to_file(*args, **kwargs):
    return get_currencies.__wrapped__(*args, **kwargs)