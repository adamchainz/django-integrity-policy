from __future__ import annotations

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from django_integrity_policy import IntegrityPolicyMiddleware

_MIDDLEWARE_PATH = "django_integrity_policy.IntegrityPolicyMiddleware"


def _middleware_is_installed() -> bool:
    middleware = getattr(settings, "MIDDLEWARE", [])
    # First: check for the exact hardcoded dotted path
    if _MIDDLEWARE_PATH in middleware:
        return True
    # Second: issubclass check to support subclassing
    for mw_path in middleware:
        try:
            mw_class = import_string(mw_path)
        except ImportError:
            continue
        try:
            if issubclass(mw_class, IntegrityPolicyMiddleware):
                return True
        except TypeError:
            continue
    return False


@register(Tags.security)
def check_settings(app_configs: object, **kwargs: object) -> list[Error]:
    errors: list[Error] = []
    checks = (
        ("INTEGRITY_POLICY", "integrity_policy.E001"),
        ("INTEGRITY_POLICY_REPORT_ONLY", "integrity_policy.E002"),
    )
    for setting_name, error_id in checks:
        value = getattr(settings, setting_name, {})
        if value:
            try:
                IntegrityPolicyMiddleware.compute_header_value(value, setting_name)
            except ImproperlyConfigured as exc:
                errors.append(Error(str(exc), id=error_id))
    return errors


@register(Tags.security)
def check_middleware_and_settings(
    app_configs: object, **kwargs: object
) -> list[Warning]:
    warnings: list[Warning] = []
    middleware_installed = _middleware_is_installed()
    has_settings = bool(getattr(settings, "INTEGRITY_POLICY", {})) or bool(
        getattr(settings, "INTEGRITY_POLICY_REPORT_ONLY", {})
    )

    if middleware_installed and not has_settings:
        warnings.append(
            Warning(
                "IntegrityPolicyMiddleware is in MIDDLEWARE but neither"
                " INTEGRITY_POLICY nor INTEGRITY_POLICY_REPORT_ONLY is configured.",
                hint=(
                    "Add an INTEGRITY_POLICY or INTEGRITY_POLICY_REPORT_ONLY setting,"
                    " or remove IntegrityPolicyMiddleware from MIDDLEWARE."
                ),
                id="integrity_policy.W001",
            )
        )
    elif not middleware_installed and has_settings:
        warnings.append(
            Warning(
                "INTEGRITY_POLICY or INTEGRITY_POLICY_REPORT_ONLY is configured but"
                " IntegrityPolicyMiddleware is not in MIDDLEWARE.",
                hint=(
                    "Add"
                    " 'django_integrity_policy.IntegrityPolicyMiddleware'"
                    " to MIDDLEWARE."
                ),
                id="integrity_policy.W002",
            )
        )
    return warnings
