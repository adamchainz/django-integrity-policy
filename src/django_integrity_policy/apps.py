from __future__ import annotations

from django.apps import AppConfig


class DjangoIntegrityPolicyConfig(AppConfig):
    name = "django_integrity_policy"
    verbose_name = "Django Integrity Policy"

    def ready(self) -> None:
        from . import checks  # noqa: F401
