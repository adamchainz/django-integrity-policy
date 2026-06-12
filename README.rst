=======================
django-integrity-policy
=======================

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/django-integrity-policy/main.yml.svg?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/django-integrity-policy/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
   :target: https://github.com/adamchainz/django-integrity-policy/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/django-integrity-policy.svg?style=for-the-badge
   :target: https://pypi.org/project/django-integrity-policy/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

----

Set the |Integrity-Policy|__ HTTP header on your Django app.

.. |Integrity-Policy| replace:: ``Integrity-Policy``
__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Integrity-Policy

----

**Work smarter and faster** with my book `Boost Your Django DX <https://adamchainz.gumroad.com/l/byddx>`__ which covers many ways to improve your development experience.

----

Requirements
------------

Python 3.10 to 3.14 supported.

Django 4.2 to 6.0 supported.

Installation
------------

1. Install with **pip**:

.. code-block:: sh

    python -m pip install django-integrity-policy

2. Optionally, add ``"django_integrity_policy"`` to your ``INSTALLED_APPS`` to enable
   `Django system checks <https://docs.djangoproject.com/en/stable/topics/checks/>`__
   that validate your settings and warn about misconfigurations:

   .. code-block:: python

       INSTALLED_APPS = [
           ...,
           "django_integrity_policy",
           ...,
       ]

3. Add the middleware in your ``MIDDLEWARE`` setting. It's best to add it
after Django's ``SecurityMiddleware``, so it adds the header at the same point
in your stack:

.. code-block:: python

    MIDDLEWARE = [
        ...,
        "django.middleware.security.SecurityMiddleware",
        "django_integrity_policy.IntegrityPolicyMiddleware",
        ...,
    ]

4. Add an ``INTEGRITY_POLICY`` or ``INTEGRITY_POLICY_REPORT_ONLY`` setting to your settings file.
   Here's an example that blocks scripts and stylesheets that lack integrity metadata:

   .. code-block:: python

       INTEGRITY_POLICY = {
           "blocked-destinations": ["script", "style"],
       }

   See below for more information on the settings.

Settings
--------

The integrity policy for your page is configured with two settings:

* ``INTEGRITY_POLICY`` - sets the |Integrity-Policy header|__, which defines the policy that the browser enforces.
* ``INTEGRITY_POLICY_REPORT_ONLY`` - sets the |Integrity-Policy-Report-Only header|__, which defines a policy that the browser simulates but does not enforce.

.. |Integrity-Policy header| replace:: ``Integrity-Policy`` header
__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Integrity-Policy

.. |Integrity-Policy-Report-Only header| replace:: ``Integrity-Policy-Report-Only`` header
__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Integrity-Policy-Report-Only

In both cases, any violations are reported to the console and optionally to a reporting endpoint defined by the |Reporting-Endpoints header|__.
The report-only header is useful for testing a new policy before enforcing it.

.. |Reporting-Endpoints header| replace:: ``Reporting-Endpoints`` header
__ https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Reporting-Endpoints

Each setting should be a dictionary with the following keys:

* ``blocked-destinations`` (required) - a list of request destinations that must include valid integrity metadata.
  Allowed values are ``'script'`` and ``'style'``.

* ``sources`` (optional) - a list of integrity metadata sources.
  The only allowed value is ``'inline'``, which is also the default when ``sources`` is omitted.

* ``endpoints`` (optional) - a list of reporting endpoint names to send violation reports to.
  The named endpoints must be defined in a ``Reporting-Endpoints`` response header.

If the keys or values are invalid, ``ImproperlyConfigured`` will be raised at instantiation time.

Examples
~~~~~~~~

Block scripts and styles that lack integrity metadata:

.. code-block:: python

    INTEGRITY_POLICY = {
        "blocked-destinations": ["script", "style"],
    }

Block scripts and report violations to a named endpoint:

.. code-block:: python

    INTEGRITY_POLICY = {
        "blocked-destinations": ["script"],
        "endpoints": ["integrity-endpoint"],
    }

Test the effect of blocking scripts without enforcing it:

.. code-block:: python

    INTEGRITY_POLICY_REPORT_ONLY = {
        "blocked-destinations": ["script"],
        "endpoints": ["integrity-endpoint"],
    }

System Checks
-------------

When ``"django_integrity_policy"`` is in ``INSTALLED_APPS``, the following
`Django system checks <https://docs.djangoproject.com/en/stable/topics/checks/>`__ are run:

* ``integrity_policy.E001`` - ``INTEGRITY_POLICY`` has invalid keys or values.
* ``integrity_policy.E002`` - ``INTEGRITY_POLICY_REPORT_ONLY`` has invalid keys or values.
* ``integrity_policy.W001`` - ``IntegrityPolicyMiddleware`` is in ``MIDDLEWARE`` but neither
  ``INTEGRITY_POLICY`` nor ``INTEGRITY_POLICY_REPORT_ONLY`` is configured.
* ``integrity_policy.W002`` - ``INTEGRITY_POLICY`` or ``INTEGRITY_POLICY_REPORT_ONLY`` is
  configured but ``IntegrityPolicyMiddleware`` is not in ``MIDDLEWARE``.

Decorators
----------

Use the below decorators to override the integrity policies (live and report-only) on a per-view basis.
The decorators fully replace the given policy set by the global settings for that view, rather than merging with it.

The examples below use function-based views.
To decorate class-based views, use the ``@method_decorator`` per `Django’s class-based view decoration documentation <https://docs.djangoproject.com/en/stable/topics/class-based-views/intro/#decorating-class-based-views>`__.

``integrity_policy_override(config)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overrides the ``Integrity-Policy`` header for the decorated view, using a dictionary
in the same format as the ``INTEGRITY_POLICY`` setting.

If ``config`` is an empty mapping (``{}``), no ``Integrity-Policy`` header will be
added to the response for that view.

For example, to block integrity-free scripts but not styles on a particular view:

.. code-block:: python

    from django.shortcuts import render
    from django_integrity_policy.decorators import integrity_policy_override


    @integrity_policy_override(
        {
            "blocked-destinations": ["script"],
        }
    )
    def drawbridge_view(request):
        return render(request, "castle/drawbridge.html")

…or, to not set an integrity policy at all on a particular view:

.. code-block:: python

    from django.shortcuts import render
    from django_integrity_policy.decorators import integrity_policy_override


    @integrity_policy_override({})
    def dungeon_view(request):
        return render(request, "castle/dungeon.html")

``integrity_policy_report_only_override(config)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overrides the ``Integrity-Policy-Report-Only`` header for the decorated view, using a
dictionary in the same format as the ``INTEGRITY_POLICY_REPORT_ONLY`` setting.

If ``config`` is an empty mapping (``{}``), no ``Integrity-Policy-Report-Only`` header
will be added to the response for that view.

For example, to test a policy that blocks integrity-free scripts and styles for a particular view:

.. code-block:: python

    from django.shortcuts import render
    from django_integrity_policy.decorators import integrity_policy_report_only_override


    @integrity_policy_report_only_override(
        {
            "blocked-destinations": ["script", "style"],
            "endpoints": ["integrity-endpoint"],
        }
    )
    def gatehouse_view(request):
        return render(request, "castle/gatehouse.html")


…or, to not set a report-only integrity policy at all on a particular view:

.. code-block:: python

    from django.shortcuts import render
    from django_integrity_policy.decorators import integrity_policy_report_only_override


    @integrity_policy_report_only_override({})
    def moat_view(request):
        return render(request, "castle/moat.html")

Adding ``integrity`` attributes
-------------------------------

Once ``Integrity-Policy`` is set, the browser will block any scripts or stylesheets (depending on configuration) that lack a valid ``integrity`` attribute, including your first-party resources.
To generate ``integrity`` attributes for your project’s static files, you can use the `django-sri package <https://pypi.org/project/django-sri/>`__, which provides template tags to generate appropriately hashed HTML tags.
For example:

.. code-block:: html+django

    {% load sri %}

    {% sri_static "app.js" %}
    {% sri_static "app.css" %}

…will output:

.. code-block:: html

    <script src="/static/app.js" integrity="sha256-..."></script>
    <link rel="stylesheet" href="/static/app.css" integrity="sha256-..."/>

These tags would be allowed per a strict integrity policy.

For a full example project, see the ``example/`` directory in this repository.
