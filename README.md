# Описание

Учебный проект: параметризуемый декоратор логирования, применённый
к функции получения курсов валют с API ЦБ РФ, и демонстрационный
пример на задаче решения квадратного уравнения.

## Цели работы

- освоить принципы разработки декораторов с параметрами;
- научиться разделять ответственность функций (бизнес-логика)
  и декораторов (сквозная логика, в частности логирование);
- научиться обрабатывать исключения, возникающие при работе
  с внешними API;
- освоить логирование в разные типы потоков
  (`sys.stdout`, `io.StringIO`, `logging`);
- научиться тестировать функцию и поведение логирования.

## Структура проекта

````

.
├── decorators.py          # Параметризуемый декоратор logger
├── currencies.py          # Бизнес-логика get_currencies (без логирования)
├── quadratic_demo.py      # Демонстрация уровней логирования
├── test_currencies.py     # Тесты (unittest)
├── requirements.txt
└── README.md

````

## Установка и запуск

````bash
# Создать и активировать виртуальное окружение
python -m venv env
source env/bin/activate        # Linux/Mac
env\Scripts\activate.bat       # Windows

# Установить зависимости
pip install -r requirements.txt
````

`requirements.txt`:

````
requests>=2.31.0
````

Запуск демонстрации:

````bash
python quadratic_demo.py
````

Запуск тестов:

````bash
python -m unittest test_currencies.py -v
````

---

## Модуль `decorators.py`

````python
from __future__ import annotations

import functools
import logging
import sys
from typing import Any, Callable, Optional, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])

HandleType = Union[Any, logging.Logger]





def _is_logger(handle: HandleType) -> bool:

    return isinstance(handle, logging.Logger)


class CriticalError:
    pass


def _resolve_level(exc: BaseException) -> str:

    if isinstance(exc, CriticalError):
        return "critical"
    if isinstance(exc, Warning):
        return "warning"
    return "error"


def logger(
    func: Optional[F] = None,
    *,
    handle: HandleType = sys.stdout,
) -> Union[F, Callable[[F], F]]:

    if func is None:
        return lambda f: logger(f, handle=handle)

    use_logging = _is_logger(handle)

    def _write(level: str, message: str) -> None:
        if use_logging:
            getattr(handle, level)(message)
        else:
            handle.write(f"{level.upper()}: {message}\n")

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:

        _write(
            "info",
            f"Вызов '{func.__name__}' c args={args}, kwargs={kwargs}",
        )
        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - логируем и пробрасываем
            level = _resolve_level(exc)
            _write(
                level,
                f"Исключение в '{func.__name__}': "
                f"{type(exc).__name__}: {exc}",
            )
            raise
        else:
            _write(
                "info",
                f"'{func.__name__}' успешно завершена, "
                f"result={result!r}",
            )
            return result

    return wrapper
````

---

## Модуль `currencies.py`

````python
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
````

---

## Модуль `solve_quadratic.py`

````python
import logging
import math
import sys
from typing import Optional, Tuple

from decorators import logger

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s: %(message)s",
)


def solve_quadratic(a: float, b: float, c: float) -> Optional[Tuple[float, ...]]:
    logging.info("Решаем %sx^2 + %sx + %s = 0", a, b, c)

    for name, value in {"a": a, "b": b, "c": c}.items():
        if not isinstance(value, (int, float)):
            logging.critical("Коэффициент %s должен быть числом", name)
            raise TypeError(f"{name} должен быть числом")

    if a == 0 and b == 0:
        logging.critical("a и b равны нулю: уравнения не существует")
        raise ValueError("a и b равны нулю")

    if a == 0:
        logging.error("a не может быть равен нулю")
        raise ValueError("a не может быть равен нулю")

    d = b ** 2 - 4 * a * c
    logging.debug("Дискриминант: %s", d)

    if d < 0:
        logging.warning("Дискриминант < 0, вещественных корней нет")
        return None

    if d == 0:
        logging.info("Один корень")
        return (-b / (2 * a),)

    root1 = (-b + math.sqrt(d)) / (2 * a)
    root2 = (-b - math.sqrt(d)) / (2 * a)
    logging.info("Два корня: %s, %s", root1, root2)
    return root1, root2


# Пример применения декоратора logger к другой функции для сравнения:
@logger(handle=sys.stdout)
def divide(a: float, b: float) -> float:
    """Простая функция для демонстрации декоратора logger."""
    return a / b


if __name__ == "__main__":
    solve_quadratic(1, -3, 2)      # INFO: два корня
    solve_quadratic(1, 1, 1)       # WARNING: d < 0
    try:
        solve_quadratic("x", 1, 1)  # CRITICAL
    except TypeError:
        pass
    try:
        solve_quadratic(0, 0, 5)    # CRITICAL
    except ValueError:
        pass

    divide(10, 2)
    try:
        divide(10, 0)               # ERROR через декоратор
    except ZeroDivisionError:
        pass
````

---

## Модуль `tests.py`

````python
import io
import unittest
from unittest.mock import patch

import requests

from currencies import get_currencies
from decorators import logger


class FakeResponse:


    def __init__(self, data, error=None):

        self.data = data
        self.error = error

    def raise_for_status(self):

        if self.error:
            raise self.error

    def json(self):

        if self.data is None:
            raise ValueError("bad json")
        return self.data


DATA = {"Valute": {"USD": {"Value": 93.25}, "BAD": {"Value": "x"}}}


class TestGetCurrencies(unittest.TestCase):


    @patch("currencies.requests.get")
    def test_success(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        self.assertEqual(get_currencies(["USD"]), {"USD": 93.25})

    @patch("currencies.requests.get")
    def test_missing_currency(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        with self.assertRaises(KeyError):
            get_currencies(["EUR"])

    @patch("currencies.requests.get")
    def test_bad_json(self, mock_get):

        mock_get.return_value = FakeResponse(None)
        with self.assertRaises(ValueError):
            get_currencies(["USD"])

    @patch("currencies.requests.get")
    def test_bad_type(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        with self.assertRaises(TypeError):
            get_currencies(["BAD"])

    @patch("currencies.requests.get")
    def test_connection_error(self, mock_get):

        mock_get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(ConnectionError):
            get_currencies(["USD"])


class TestLogger(unittest.TestCase):


    def setUp(self):

        self.stream = io.StringIO()

        @logger(handle=self.stream)
        def ok(x):
            return x * 2

        @logger(handle=self.stream)
        def bad():
            raise ValueError("boom")

        self.ok = ok
        self.bad = bad

    def test_success_logging(self):

        self.assertEqual(self.ok(2), 4)
        logs = self.stream.getvalue()
        self.assertIn("INFO", logs)
        self.assertIn("4", logs)

    def test_error_logging(self):

        with self.assertRaises(ValueError):
            self.bad()
        logs = self.stream.getvalue()
        self.assertRegex(logs, "ERROR")
        self.assertIn("ValueError", logs)


class TestStreamWrite(unittest.TestCase):


    def setUp(self):

        self.stream = io.StringIO()

        @logger(handle=self.stream)
        def wrapped():
            return get_currencies(["USD"], url="https://invalid.invalid")

        self.wrapped = wrapped

    def test_logging_error(self):

        with self.assertRaises(ConnectionError):
            self.wrapped()
        logs = self.stream.getvalue()
        self.assertIn("ERROR", logs)
        self.assertIn("ConnectionError", logs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
````

---

## Ответ на контрольный вопрос

**Как логировать ошибки внутри функции, если логирование вынесено в декоратор?**

Функция не обращается к объекту логирования напрямую — она лишь
**выбрасывает исключение**, а декоратор его перехватывает и
записывает в лог. Если стандартной схемы «успех → INFO, ошибка →
ERROR» недостаточно, есть два простых решения:

1. **Различать уровень по типу исключения.** Декоратор может
   проверять `isinstance(exc, Warning)` и логировать такие случаи
   как `WARNING`, а остальные исключения — как `ERROR`. Функция
   при этом просто выбирает подходящий тип исключения, не трогая
   логирование напрямую.
2. **Логировать напрямую внутри функции своим логгером**, если
   нужна более тонкая гранулярность (DEBUG/WARNING/CRITICAL по ходу
   вычислений, а не только по факту успеха/ошибки) — как это
   сделано в `solve_quadratic`. В таком случае разделение
   ответственности выглядит так: декоратор логирует *факт вызова,
   результат и необработанные исключения*, а сама функция —
   *специфичную для её логики диагностическую информацию*.

## Требования к окружению

````bash
pip install requests
````

Рекомендуется работать в виртуальном окружении:

````bash
python -m venv env
source env/bin/activate      # Linux/Mac
env\Scripts\activate.bat     # Windows
````

## Лицензия

Учебный проект, распространяется свободно.

````

Если нужно — могу также оформить каждый файл (`decorators.py`, `currencies.py` и т.д.) отдельно с полными docstring'ами внутри самого кода (не только в README), чтобы `help()` и `pydoc` отображали документацию корректно.
````
