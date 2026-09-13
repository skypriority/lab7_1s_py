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
        except Exception as exc:
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
