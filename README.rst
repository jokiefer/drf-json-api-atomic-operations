.. image:: https://readthedocs.org/projects/drf-json-api-atomic-operations/badge/?version=latest
    :target: https://drf-json-api-atomic-operations.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/drf-json-api-atomic-operations.svg
    :target: https://pypi.org/project/drf-json-api-atomic-operations/
    :alt: PyPi version


drf-json-api-atomic-operation
=============================

Extension for `django-rest-framework-json-api <https://github.com/django-json-api/django-rest-framework-json-api>`_ to support `atomic operations <https://jsonapi.org/ext/atomic/>`_.

See the `usage <https://drf-json-api-atomic-operations.readthedocs.io/en/latest/usage.html>`_ section of the docs for example integration.



Implemented Features
~~~~~~~~~~~~~~~~~~~~

* creating, updating, removing multiple resources in a single request (sequential db calls optional bulk db calls for create and delete)
* `Updating To-One Relationships <https://jsonapi.org/ext/atomic/#auto-id-updating-to-one-relationships>`_
* `Updating To-Many Relationships <https://jsonapi.org/ext/atomic/#auto-id-updating-to-many-relationships>`_
* error reporting with json pointer to the concrete operation and the wrong attributes


ToDo
~~~~

* permission handling
* `local identity (lid) <https://jsonapi.org/ext/atomic/#operation-objects>`_ handling
