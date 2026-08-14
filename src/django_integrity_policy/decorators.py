from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, TypeVar

from django.http import HttpRequest, HttpResponseBase

from django_integrity_policy import IntegrityPolicyMiddleware

_ViewFunc = TypeVar(
    "_ViewFunc",
    bound=Callable[..., Any],
)


def _make_decorator(
    attr_name: str, header_value: str
) -> Callable[[_ViewFunc], _ViewFunc]:
    def decorator(view_func: _ViewFunc) -> _ViewFunc:
        if iscoroutinefunction(view_func):

            @wraps(view_func)
            async def async_wrapper(
                request: HttpRequest, *args: Any, **kwargs: Any
            ) -> HttpResponseBase:
                response = await view_func(request, *args, **kwargs)
                setattr(response, attr_name, header_value)
                return response  # type: ignore[no-any-return]

            return async_wrapper  # type: ignore[return-value]
        else:

            @wraps(view_func)
            def sync_wrapper(
                request: HttpRequest, *args: Any, **kwargs: Any
            ) -> HttpResponseBase:
                response = view_func(request, *args, **kwargs)
                setattr(response, attr_name, header_value)
                return response  # type: ignore[no-any-return]

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def integrity_policy_override(
    config: dict[str, list[str]],
) -> Callable[[_ViewFunc], _ViewFunc]:
    header_value = IntegrityPolicyMiddleware.compute_header_value(
        config, name="integrity_policy_override"
    )
    return _make_decorator("_integrity_policy_override", header_value)


def integrity_policy_report_only_override(
    config: dict[str, list[str]],
) -> Callable[[_ViewFunc], _ViewFunc]:
    header_value = IntegrityPolicyMiddleware.compute_header_value(
        config, name="integrity_policy_report_only_override"
    )
    return _make_decorator("_integrity_policy_report_only_override", header_value)
