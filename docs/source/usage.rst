.. _usage:


Usage
=====


To provide an atomic operations api you need to define a new view based on the `AtomicOperationView` class:

.. code-block:: python
   
   from atomic_operations.views import AtomicOperationView

   class ConcretAtomicOperationView(AtomicOperationView):

      # Define the serializers for any operation you want to provide by the view
      serializer_classes = {
         "add:BasicModel": BasicModelSerializer,
         "update:BasicModel": BasicModelSerializer,
         "remove:BasicModel": BasicModelSerializer,
      }


Then register the new defined view as any other view in your django project:

.. code-block:: python

   from django.urls import path

   from tests.views import ConcretAtomicOperationView

   urlpatterns = [
      path("atomic-operations", ConcretAtomicOperationView.as_view())
   ]

Now you can call the api like below.

.. code-block:: http 

   POST /atomic-operations HTTP/1.1
   Host: example.org
   Content-Type: application/vnd.api+json;ext="https://jsonapi.org/ext/atomic"
   Accept: application/vnd.api+json;ext="https://jsonapi.org/ext/atomic"

   {
      "atomic:operations": [{
         "op": "add",
         "data": {
            "type": "BasicModel",
            "attributes": {
               "title": "JSON API paints my bikeshed!"
            }
         }
      }]
   }


.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: application/vnd.api+json;ext="https://jsonapi.org/ext/atomic"

   {
      "atomic:results": [{
         "data": {
            "links": {
            "self": "http://example.com/basicmodel/13"
            },
            "type": "BasicModel",
            "id": "13",
            "attributes": {
            "title": "JSON API paints my bikeshed!"
            }
         }
      }]
   }


Bulk operating
==============

By default all operations are sequential db calls. This package provides also bulk operating for creating and deleting resources. To activate it you need to configure the following.


.. code-block:: python
   
   from atomic_operations.views import AtomicOperationView

   class ConcretAtomicOperationView(AtomicOperationView):

      sequential = False
