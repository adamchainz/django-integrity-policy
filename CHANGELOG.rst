=========
Changelog
=========

1.2.0 (2026-08-14)
------------------

* Support Python 3.15.

* Add Django 6.1 support.

* Drop Django 4.2 to 5.1 support.

* Add ``policy`` and ``report_only_policy`` keyword-only arguments to ``IntegrityPolicyMiddleware.__init__()``, which take precedence over the ``INTEGRITY_POLICY`` and ``INTEGRITY_POLICY_REPORT_ONLY`` settings.
  This allows composing several differently-configured instances, such as to send a different policy for admin pages.

  `PR #17 <https://github.com/adamchainz/django-integrity-policy/pull/17>`__.

* Switch package build backend from setuptools to `uv_build <https://docs.astral.sh/uv/concepts/build-backend/>`__.
  This makes builds with uv about nine times faster, since uv runs the backend natively, without creating a build environment or spawning a Python process.
  Additionally, source distributions no longer include test files, which setuptools previously included incompletely, missing the files needed to actually run them.

1.1.0 (2026-06-12)
------------------

* Added decorators for per-view header control: ``@integrity_policy_override`` and ``@integrity_policy_report_only_override``.

1.0.0 (2026-05-28)
------------------

* Initial release.
