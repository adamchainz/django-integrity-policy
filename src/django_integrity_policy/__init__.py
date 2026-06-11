from __future__ import annotations

from collections.abc import Awaitable, Callable

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.utils.functional import cached_property

_BLOCKED_DESTINATIONS: frozenset[str] = frozenset({"script", "style"})
_SOURCES: frozenset[str] = frozenset({"inline"})
_VALID_KEYS: frozenset[str] = frozenset(
    {"blocked-destinations", "sources", "endpoints"}
)


class IntegrityPolicyMiddleware:
    sync_capable = True
    async_capable = True

    def __init__(
        self,
        get_response: (
            Callable[[HttpRequest], HttpResponseBase]
            | Callable[[HttpRequest], Awaitable[HttpResponseBase]]
        ),
    ) -> None:
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

        if self.async_mode:
            # Mark the class as async-capable, but do the actual switch
            # inside __call__ to avoid swapping out dunder methods
            markcoroutinefunction(self)

        self.integrity_policy  # noqa: B018 - Access at setup so ImproperlyConfigured can be raised
        self.integrity_policy_report_only  # noqa: B018 - Access at setup so ImproperlyConfigured can be raised
        receiver(setting_changed)(self.clear_header_value)

    def __call__(
        self, request: HttpRequest
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        if self.async_mode:
            return self.__acall__(request)
        response = self.get_response(request)
        assert isinstance(response, HttpResponseBase)  # type narrow
        return self._apply_headers(response)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        result = self.get_response(request)
        assert not isinstance(result, HttpResponseBase)  # type narrow
        response = await result
        return self._apply_headers(response)

    def _apply_headers(self, response: HttpResponseBase) -> HttpResponseBase:
        if hasattr(response, "_integrity_policy_override"):
            if response._integrity_policy_override:
                response["Integrity-Policy"] = response._integrity_policy_override
        elif value := self.integrity_policy:
            response["Integrity-Policy"] = value

        if hasattr(response, "_integrity_policy_report_only_override"):
            if response._integrity_policy_report_only_override:
                response["Integrity-Policy-Report-Only"] = (
                    response._integrity_policy_report_only_override
                )
        elif value := self.integrity_policy_report_only:
            response["Integrity-Policy-Report-Only"] = value

        return response

    @cached_property
    def integrity_policy(self) -> str:
        return self.compute_header_value(
            getattr(settings, "INTEGRITY_POLICY", {}),
            setting_name="INTEGRITY_POLICY",
        )

    @cached_property
    def integrity_policy_report_only(self) -> str:
        return self.compute_header_value(
            getattr(settings, "INTEGRITY_POLICY_REPORT_ONLY", {}),
            setting_name="INTEGRITY_POLICY_REPORT_ONLY",
        )

    @staticmethod
    def compute_header_value(
        setting: dict[str, list[str]],
        setting_name: str,
    ) -> str:
        if not setting:
            return ""

        unknown_keys = set(setting.keys()) - _VALID_KEYS
        if unknown_keys:
            raise ImproperlyConfigured(
                f"Unknown key(s) in {setting_name}: {', '.join(sorted(unknown_keys))}"
            )

        blocked_destinations = setting.get("blocked-destinations") or []
        if not blocked_destinations:
            raise ImproperlyConfigured(
                f"{setting_name} must include 'blocked-destinations' with at least one value"
            )
        for dest in blocked_destinations:
            if dest not in _BLOCKED_DESTINATIONS:
                raise ImproperlyConfigured(
                    f"Unknown blocked-destination '{dest}' in {setting_name}"
                )

        pieces = ["blocked-destinations=(" + " ".join(blocked_destinations) + ")"]

        sources = setting.get("sources")
        if sources is not None:
            for src in sources:
                if src not in _SOURCES:
                    raise ImproperlyConfigured(
                        f"Unknown source '{src}' in {setting_name}"
                    )
            pieces.append("sources=(" + " ".join(sources) + ")")

        endpoints = setting.get("endpoints")
        if endpoints:
            pieces.append("endpoints=(" + " ".join(endpoints) + ")")

        return ", ".join(pieces)

    def clear_header_value(self, setting: str, **kwargs: object) -> None:
        if setting == "INTEGRITY_POLICY":
            try:
                del self.integrity_policy
            except AttributeError:
                pass
        elif setting == "INTEGRITY_POLICY_REPORT_ONLY":
            try:
                del self.integrity_policy_report_only
            except AttributeError:
                pass
