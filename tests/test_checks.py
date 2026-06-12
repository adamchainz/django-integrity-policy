from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from django_integrity_policy.checks import check_middleware_and_settings, check_settings


class CheckSettingsTests(SimpleTestCase):
    def test_no_settings(self):
        errors = check_settings(None)
        assert errors == []

    @override_settings(INTEGRITY_POLICY={"blocked-destinations": ["script"]})
    def test_valid_integrity_policy(self):
        errors = check_settings(None)
        assert errors == []

    @override_settings(
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]}
    )
    def test_valid_report_only(self):
        errors = check_settings(None)
        assert errors == []

    @override_settings(INTEGRITY_POLICY={})
    def test_empty_integrity_policy_no_error(self):
        errors = check_settings(None)
        assert errors == []

    @override_settings(INTEGRITY_POLICY_REPORT_ONLY={})
    def test_empty_report_only_no_error(self):
        errors = check_settings(None)
        assert errors == []

    @override_settings(INTEGRITY_POLICY={"blocked-destinations": ["unknown"]})
    def test_invalid_blocked_destination_integrity_policy(self):
        errors = check_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "integrity_policy.E001"
        assert "INTEGRITY_POLICY" in errors[0].msg

    @override_settings(
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["unknown"]}
    )
    def test_invalid_blocked_destination_report_only(self):
        errors = check_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "integrity_policy.E002"
        assert "INTEGRITY_POLICY_REPORT_ONLY" in errors[0].msg

    @override_settings(
        INTEGRITY_POLICY={"blocked-destinations": ["script"], "bad-key": ["value"]}
    )
    def test_unknown_key_integrity_policy(self):
        errors = check_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "integrity_policy.E001"

    @override_settings(INTEGRITY_POLICY={"endpoints": ["endpoint"]})
    def test_missing_blocked_destinations(self):
        errors = check_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "integrity_policy.E001"

    @override_settings(
        INTEGRITY_POLICY={"blocked-destinations": ["script"], "sources": ["bad"]}
    )
    def test_invalid_source_integrity_policy(self):
        errors = check_settings(None)
        assert len(errors) == 1
        assert errors[0].id == "integrity_policy.E001"

    @override_settings(
        INTEGRITY_POLICY={"blocked-destinations": ["unknown"]},
        INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["also-unknown"]},
    )
    def test_both_settings_invalid_returns_two_errors(self):
        errors = check_settings(None)
        assert len(errors) == 2
        ids = {e.id for e in errors}
        assert ids == {"integrity_policy.E001", "integrity_policy.E002"}


class CheckMiddlewareAndSettingsTests(SimpleTestCase):
    def test_neither_middleware_nor_settings(self):
        with override_settings(MIDDLEWARE=[]):
            warnings = check_middleware_and_settings(None)
        assert warnings == []

    def test_middleware_and_settings(self):
        with override_settings(
            MIDDLEWARE=["django_integrity_policy.IntegrityPolicyMiddleware"],
            INTEGRITY_POLICY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert warnings == []

    def test_middleware_and_report_only_settings(self):
        with override_settings(
            MIDDLEWARE=["django_integrity_policy.IntegrityPolicyMiddleware"],
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert warnings == []

    def test_middleware_without_settings(self):
        with override_settings(
            MIDDLEWARE=["django_integrity_policy.IntegrityPolicyMiddleware"],
        ):
            warnings = check_middleware_and_settings(None)
        assert len(warnings) == 1
        assert warnings[0].id == "integrity_policy.W001"

    def test_middleware_with_empty_settings(self):
        with override_settings(
            MIDDLEWARE=["django_integrity_policy.IntegrityPolicyMiddleware"],
            INTEGRITY_POLICY={},
            INTEGRITY_POLICY_REPORT_ONLY={},
        ):
            warnings = check_middleware_and_settings(None)
        assert len(warnings) == 1
        assert warnings[0].id == "integrity_policy.W001"

    def test_settings_without_middleware(self):
        with override_settings(
            MIDDLEWARE=[],
            INTEGRITY_POLICY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert len(warnings) == 1
        assert warnings[0].id == "integrity_policy.W002"

    def test_report_only_without_middleware(self):
        with override_settings(
            MIDDLEWARE=[],
            INTEGRITY_POLICY_REPORT_ONLY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert len(warnings) == 1
        assert warnings[0].id == "integrity_policy.W002"

    def test_subclassed_middleware_detected(self):
        with override_settings(
            MIDDLEWARE=[
                "tests.testapp.middleware.SubclassedIntegrityPolicyMiddleware"
            ],
            INTEGRITY_POLICY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert warnings == []

    def test_subclassed_middleware_without_settings_warns(self):
        with override_settings(
            MIDDLEWARE=[
                "tests.testapp.middleware.SubclassedIntegrityPolicyMiddleware"
            ],
        ):
            warnings = check_middleware_and_settings(None)
        assert len(warnings) == 1
        assert warnings[0].id == "integrity_policy.W001"

    def test_unimportable_middleware_skipped(self):
        with override_settings(
            MIDDLEWARE=[
                "does.not.exist.SomeMiddleware",
                "django_integrity_policy.IntegrityPolicyMiddleware",
            ],
            INTEGRITY_POLICY={"blocked-destinations": ["script"]},
        ):
            warnings = check_middleware_and_settings(None)
        assert warnings == []
