from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from django_integrity_policy.decorators import (
    integrity_policy_override,
    integrity_policy_report_only_override,
)


class IntegrityPolicyOverrideTests(SimpleTestCase):
    def test_override_sets_header(self):
        resp = self.client.get("/override/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    def test_override_replaces_global_setting(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["style"]}):
            resp = self.client.get("/override/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    def test_override_empty_disables_header(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            resp = self.client.get("/override-disabled/")

        assert "Integrity-Policy" not in resp

    def test_override_does_not_affect_report_only(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]}
        ):
            resp = self.client.get("/override/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    def test_override_invalid_config_raises(self):
        with pytest.raises(ImproperlyConfigured):
            integrity_policy_override({"blocked-destinations": ["unknown"]})

    async def test_async_override_sets_header(self):
        resp = await self.async_client.get("/async/override/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    async def test_async_override_empty_disables_header(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            resp = await self.async_client.get("/async/override-disabled/")

        assert "Integrity-Policy" not in resp


class IntegrityPolicyReportOnlyOverrideTests(SimpleTestCase):
    def test_report_only_override_sets_header(self):
        resp = self.client.get("/report-only-override/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    def test_report_only_override_replaces_global_setting(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]}
        ):
            resp = self.client.get("/report-only-override/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    def test_report_only_override_empty_disables_header(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
        ):
            resp = self.client.get("/report-only-override-disabled/")

        assert "Integrity-Policy-Report-Only" not in resp

    def test_report_only_override_does_not_affect_enforced(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["style"]}):
            resp = self.client.get("/report-only-override/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(style)"

    def test_report_only_override_invalid_config_raises(self):
        with pytest.raises(ImproperlyConfigured):
            integrity_policy_report_only_override({"blocked-destinations": ["unknown"]})

    async def test_async_report_only_override_sets_header(self):
        resp = await self.async_client.get("/async/report-only-override/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    async def test_async_report_only_override_empty_disables_header(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
        ):
            resp = await self.async_client.get("/async/report-only-override-disabled/")

        assert "Integrity-Policy-Report-Only" not in resp
