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
        *,
        policy: dict[str, list[str]] | None = None,
        report_only_policy: dict[str, list[str]] | None = None,
    ) -> None:
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

        if self.async_mode:
            # Mark the class as async-capable, but do the actual switch
            # inside __call__ to avoid swapping out dunder methods
            markcoroutinefunction(self)

        # Values from arguments can never change, so compute eagerly. This also
        # validates them, like the eager access of the setting-based values below.
        if policy is not None:
            self.integrity_policy = self.compute_header_value(
                policy, name="'policy' argument"
            )
        else:
            self.integrity_policy  # noqa: B018 - Access at setup so ImproperlyConfigured can be raised

        if report_only_policy is not None:
            self.integrity_policy_report_only = self.compute_header_value(
                report_only_policy, name="'report_only_policy' argument"
            )
        else:
            self.integrity_policy_report_only  # noqa: B018 - Access at setup so ImproperlyConfigured can be raised

        self.policy_from_argument = policy is not None
        self.report_only_policy_from_argument = report_only_policy is not None

        if not (self.policy_from_argument and self.report_only_policy_from_argument):
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
            name="INTEGRITY_POLICY",
        )

    @cached_property
    def integrity_policy_report_only(self) -> str:
        return self.compute_header_value(
            getattr(settings, "INTEGRITY_POLICY_REPORT_ONLY", {}),
            name="INTEGRITY_POLICY_REPORT_ONLY",
        )

    @staticmethod
    def compute_header_value(
        policy: dict[str, list[str]],
        name: str,
    ) -> str:
        if not policy:
            return ""

        unknown_keys = set(policy.keys()) - _VALID_KEYS
        if unknown_keys:
            raise ImproperlyConfigured(
                f"Unknown key(s) in {name}: {', '.join(sorted(unknown_keys))}"
            )

        blocked_destinations = policy.get("blocked-destinations") or []
        if not blocked_destinations:
            raise ImproperlyConfigured(
                f"{name} must include 'blocked-destinations' with at least one value"
            )
        for dest in blocked_destinations:
            if dest not in _BLOCKED_DESTINATIONS:
                raise ImproperlyConfigured(
                    f"Unknown blocked-destination '{dest}' in {name}"
                )

        pieces = ["blocked-destinations=(" + " ".join(blocked_destinations) + ")"]

        sources = policy.get("sources")
        if sources is not None:
            for src in sources:
                if src not in _SOURCES:
                    raise ImproperlyConfigured(f"Unknown source '{src}' in {name}")
            pieces.append("sources=(" + " ".join(sources) + ")")

        endpoints = policy.get("endpoints")
        if endpoints:
            pieces.append("endpoints=(" + " ".join(endpoints) + ")")

        return ", ".join(pieces)

    def clear_header_value(self, setting: str, **kwargs: object) -> None:
        if setting == "INTEGRITY_POLICY":
            if self.policy_from_argument:
                return
            try:
                del self.integrity_policy
            except AttributeError:
                pass
        elif setting == "INTEGRITY_POLICY_REPORT_ONLY":
            if self.report_only_policy_from_argument:
                return
            try:
                del self.integrity_policy_report_only
            except AttributeError:
                pass
