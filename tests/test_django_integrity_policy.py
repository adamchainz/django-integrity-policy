from __future__ import annotations

from http import HTTPStatus

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings


class IntegrityPolicyMiddlewareTests(SimpleTestCase):
    def test_index(self):
        resp = self.client.get("/")

        assert resp.status_code == HTTPStatus.OK
        assert resp.content == b"Hello World"

    def test_no_settings(self):
        resp = self.client.get("/")

        assert "Integrity-Policy" not in resp

    def test_empty_setting(self):
        with override_settings(INTEGRITY_POLICY={}):
            resp = self.client.get("/")

        assert "Integrity-Policy" not in resp

    def test_empty_report_only_setting(self):
        with override_settings(INTEGRITY_POLICY_REPORT_ONLY={}):
            resp = self.client.get("/")

        assert "Integrity-Policy-Report-Only" not in resp

    def test_script_blocked(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            resp = self.client.get("/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    def test_style_blocked(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["style"]}):
            resp = self.client.get("/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(style)"

    def test_multiple_destinations_blocked(self):
        with override_settings(
            INTEGRITY_POLICY={"blocked-destinations": ["script", "style"]}
        ):
            resp = self.client.get("/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script style)"

    def test_with_endpoints(self):
        with override_settings(
            INTEGRITY_POLICY={
                "blocked-destinations": ["script"],
                "endpoints": ["integrity-endpoint", "backup-endpoint"],
            }
        ):
            resp = self.client.get("/")

        assert (
            resp["Integrity-Policy"]
            == "blocked-destinations=(script), endpoints=(integrity-endpoint backup-endpoint)"
        )

    def test_with_sources(self):
        with override_settings(
            INTEGRITY_POLICY={
                "blocked-destinations": ["script"],
                "sources": ["inline"],
            }
        ):
            resp = self.client.get("/")

        assert (
            resp["Integrity-Policy"]
            == "blocked-destinations=(script), sources=(inline)"
        )

    def test_all_fields(self):
        with override_settings(
            INTEGRITY_POLICY={
                "blocked-destinations": ["script", "style"],
                "sources": ["inline"],
                "endpoints": ["integrity-endpoint"],
            }
        ):
            resp = self.client.get("/")

        assert (
            resp["Integrity-Policy"]
            == "blocked-destinations=(script style), sources=(inline), endpoints=(integrity-endpoint)"
        )

    def test_unknown_blocked_destination(self):
        with (
            override_settings(INTEGRITY_POLICY={"blocked-destinations": ["unknown"]}),
            pytest.raises(ImproperlyConfigured),
        ):
            self.client.get("/")

    def test_unknown_source(self):
        with (
            override_settings(
                INTEGRITY_POLICY={
                    "blocked-destinations": ["script"],
                    "sources": ["unknown"],
                }
            ),
            pytest.raises(ImproperlyConfigured),
        ):
            self.client.get("/")

    def test_unknown_key(self):
        with (
            override_settings(
                INTEGRITY_POLICY={
                    "blocked-destinations": ["script"],
                    "bad-key": ["value"],
                }
            ),
            pytest.raises(ImproperlyConfigured),
        ):
            self.client.get("/")

    def test_missing_blocked_destinations(self):
        with (
            override_settings(INTEGRITY_POLICY={"endpoints": ["integrity-endpoint"]}),
            pytest.raises(ImproperlyConfigured),
        ):
            self.client.get("/")

    def test_report_only(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
        ):
            resp = self.client.get("/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    def test_report_only_all_fields(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={
                "blocked-destinations": ["script", "style"],
                "sources": ["inline"],
                "endpoints": ["integrity-endpoint"],
            }
        ):
            resp = self.client.get("/")

        assert (
            resp["Integrity-Policy-Report-Only"]
            == "blocked-destinations=(script style), sources=(inline), endpoints=(integrity-endpoint)"
        )

    def test_setting_changing(self):
        with override_settings(INTEGRITY_POLICY={}):
            self.client.get("/")  # Forces middleware instantiation

        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            resp = self.client.get("/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    def test_report_only_setting_changing(self):
        with override_settings(INTEGRITY_POLICY_REPORT_ONLY={}):
            self.client.get("/")  # Forces middleware instantiation

        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
        ):
            resp = self.client.get("/")

        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    def test_other_setting_changing(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            self.client.get("/")  # Forces middleware instantiation

            with override_settings(SECRET_KEY="foobar"):
                resp = self.client.get("/")

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    async def test_async_no_settings(self):
        resp = await self.async_client.get("/async/")

        assert resp.status_code == HTTPStatus.OK
        assert "Integrity-Policy" not in resp
        assert "Integrity-Policy-Report-Only" not in resp

    async def test_async(self):
        with override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]}):
            resp = await self.async_client.get("/async/")

        assert resp.status_code == HTTPStatus.OK
        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"

    async def test_async_report_only(self):
        with override_settings(
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
        ):
            resp = await self.async_client.get("/async/")

        assert resp.status_code == HTTPStatus.OK
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"
