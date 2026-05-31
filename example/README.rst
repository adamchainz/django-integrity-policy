Example Application
===================

Run with:

.. code-block:: sh

   uv run --group example manage.py runserver

Open it at http://127.0.0.1:8000/ .

The app sets a strict ``Integrity-Policy`` header using ``IntegrityPolicyMiddleware``.
The included CSS and JS files are hashed with `django-sri <https://pypi.org/project/django-sri/>`__ template tags, which generate ``integrity`` attributes for each file.

Open the network tab in your browser's devtools to see the header and the hashed ``integrity`` attributes on the static file tags.
