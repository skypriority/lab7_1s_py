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

@logger(handle=sys.stdout)
def divide(a: float, b: float) -> float:
    """Простая функция для демонстрации декоратора logger."""
    return a / b


if __name__ == "__main__":
    solve_quadratic(1, -3, 2)
    solve_quadratic(1, 1, 1)
    try:
        solve_quadratic("x", 1, 1)
    except TypeError:
        pass
    try:
        solve_quadratic(0, 0, 5)
    except ValueError:
        pass

    divide(10, 2)
    try:
        divide(10, 0)
    except ZeroDivisionError:
        pass
