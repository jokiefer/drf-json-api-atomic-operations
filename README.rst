drf-json-api-atomic-operation
=============================

Extension for `django-rest-framework-json-api <https://github.com/django-json-api/django-rest-framework-json-api>`_ to support `atomic operations <https://jsonapi.org/ext/atomic/>`_.

See the `usage` section of the docs for example integration.



Implemented Features
~~~~~~~~~~~~~~~~~~~~

* creating, updating, removing multiple resources in a single request (sequential db calls)
* error reporting with json pointer to the concrete operation and the wrong attributes


ToDo
~~~~

* permission handling
* use django bulk operations to optimize db execution time
* `local identity (lid) <https://jsonapi.org/ext/atomic/#operation-objects>`_ handling
* `Updating To-One Relationships <https://jsonapi.org/ext/atomic/#auto-id-updating-to-one-relationships>`_
* `Updating To-Many Relationships <https://jsonapi.org/ext/atomic/#auto-id-updating-to-many-relationships>`_

