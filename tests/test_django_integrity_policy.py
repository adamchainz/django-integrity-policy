from __future__ import annotations

from collections.abc import Awaitable
from http import HTTPStatus

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseBase
from django.test import RequestFactory, SimpleTestCase, override_settings

from django_integrity_policy import IntegrityPolicyMiddleware


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
            pytest.raises(
                ImproperlyConfigured,
                match="Unknown blocked-destination 'unknown' in INTEGRITY_POLICY",
            ),
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
            pytest.raises(
                ImproperlyConfigured,
                match="Unknown source 'unknown' in INTEGRITY_POLICY",
            ),
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
            pytest.raises(
                ImproperlyConfigured,
                match="Unknown key\\(s\\) in INTEGRITY_POLICY: bad-key",
            ),
        ):
            self.client.get("/")

    def test_missing_blocked_destinations(self):
        with (
            override_settings(INTEGRITY_POLICY={"endpoints": ["integrity-endpoint"]}),
            pytest.raises(
                ImproperlyConfigured,
                match="INTEGRITY_POLICY must include 'blocked-destinations' with at least one value",
            ),
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


class IntegrityPolicyMiddlewareArgumentTests(SimpleTestCase):
    request_factory = RequestFactory()

    def get_response(self, request):
        return HttpResponse("Hello World")

    async def aget_response(self, request):
        return HttpResponse("Hello World")

    @override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]})
    def test_policy_argument_used_instead_of_setting(self):
        middleware = IntegrityPolicyMiddleware(
            self.get_response, policy={"blocked-destinations": ["style"]}
        )

        resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(style)"

    @override_settings(
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
    )
    def test_report_only_policy_argument_used_instead_of_setting(self):
        middleware = IntegrityPolicyMiddleware(
            self.get_response, report_only_policy={"blocked-destinations": ["style"]}
        )

        resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    @override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]})
    def test_empty_policy_argument_sends_no_header(self):
        middleware = IntegrityPolicyMiddleware(self.get_response, policy={})

        resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert "Integrity-Policy" not in resp

    @override_settings(
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
    )
    def test_empty_report_only_policy_argument_sends_no_header(self):
        middleware = IntegrityPolicyMiddleware(self.get_response, report_only_policy={})

        resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert "Integrity-Policy-Report-Only" not in resp

    @override_settings(
        INTEGRITY_POLICY={"blocked-destinations": ["script"]},
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]},
    )
    def test_none_falls_back_to_settings(self):
        middleware = IntegrityPolicyMiddleware(self.get_response)

        resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    def test_invalid_policy_argument(self):
        with pytest.raises(
            ImproperlyConfigured,
            match="Unknown blocked-destination 'font' in 'policy' argument",
        ):
            IntegrityPolicyMiddleware(
                self.get_response, policy={"blocked-destinations": ["font"]}
            )

    def test_invalid_report_only_policy_argument(self):
        with pytest.raises(
            ImproperlyConfigured,
            match="Unknown blocked-destination 'font' in 'report_only_policy' argument",
        ):
            IntegrityPolicyMiddleware(
                self.get_response, report_only_policy={"blocked-destinations": ["font"]}
            )

    def test_override_settings_affects_setting_sourced_instance(self):
        middleware = IntegrityPolicyMiddleware(self.get_response)

        with override_settings(
            INTEGRITY_POLICY={"blocked-destinations": ["script"]},
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]},
        ):
            resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    def test_override_settings_does_not_affect_argument_sourced_instance(self):
        middleware = IntegrityPolicyMiddleware(
            self.get_response,
            policy={"blocked-destinations": ["script"]},
            report_only_policy={"blocked-destinations": ["style"]},
        )

        with override_settings(
            INTEGRITY_POLICY={"blocked-destinations": ["style"]},
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]},
        ):
            resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    def test_override_settings_with_only_policy_from_argument(self):
        middleware = IntegrityPolicyMiddleware(
            self.get_response, policy={"blocked-destinations": ["script"]}
        )

        with override_settings(
            INTEGRITY_POLICY={"blocked-destinations": ["style"]},
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]},
        ):
            resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"

    def test_override_settings_with_only_report_only_policy_from_argument(self):
        middleware = IntegrityPolicyMiddleware(
            self.get_response, report_only_policy={"blocked-destinations": ["script"]}
        )

        with override_settings(
            INTEGRITY_POLICY={"blocked-destinations": ["style"]},
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["style"]},
        ):
            resp = middleware(self.request_factory.get("/"))

        assert isinstance(resp, HttpResponseBase)
        assert resp["Integrity-Policy"] == "blocked-destinations=(style)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(script)"

    @override_settings(INTEGRITY_POLICY={"blocked-destinations": ["style"]})
    async def test_async_policy_argument(self):
        middleware = IntegrityPolicyMiddleware(
            self.aget_response,
            policy={"blocked-destinations": ["script"]},
            report_only_policy={"blocked-destinations": ["style"]},
        )

        coroutine = middleware(self.request_factory.get("/"))
        assert isinstance(coroutine, Awaitable)
        resp = await coroutine
        assert isinstance(resp, HttpResponseBase)

        assert resp["Integrity-Policy"] == "blocked-destinations=(script)"
        assert resp["Integrity-Policy-Report-Only"] == "blocked-destinations=(style)"
