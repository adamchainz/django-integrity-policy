=========
Changelog
=========

1.2.0 (2026-06-12)
------------------

* Added Django system checks that validate ``INTEGRITY_POLICY`` and ``INTEGRITY_POLICY_REPORT_ONLY`` settings and warn when middleware and settings are mismatched.
  Add ``"django_integrity_policy"`` to ``INSTALLED_APPS`` to enable them.

1.1.0 (2026-06-12)
------------------

* Added decorators for per-view header control: ``@integrity_policy_override`` and ``@integrity_policy_report_only_override``.

1.0.0 (2026-05-28)
------------------

* Initial release.
