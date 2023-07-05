import json

from django.test import Client, RequestFactory, TestCase

from tests.models import BasicModel
from tests.views import ConcretAtomicOperationView


class TestAtomicOperationView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ConcretAtomicOperationView
        self.client = Client()

        self.maxDiff = None
    # def test_view(self):
    #     data = {
    #         "atomic:operations": [
    #             {
    #                 "op": "add",
    #                 "data": {
    #                     "type": "BasicModel",
    #                     "attributes": {
    #                         "text": "JSON API paints my bikeshed!"
    #                     }
    #                 }
    #             }, {
    #                 "op": "update",
    #                 "data": {
    #                     "id": "1",
    #                     "type": "BasicModel",
    #                     "attributes": {
    #                         "text": "JSON API paints my bikeshed2!"
    #                     }
    #                 }
    #             }
    #         ]
    #     }
    #     post_request = self.factory.post(
    #         path="/",
    #         data=data,
    #         content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',
    #         **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
    #     )
    #     response = self.view.as_view()(post_request)

    def test_view_processing(self):
        operations = [
            {
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "update",
                "data": {
                    "id": "1",
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed2!"
                    }
                }
            }, {
                "op": "remove",
                "ref": {
                    "id": "1",
                    "type": "BasicModel",
                }
            }
        ]

        data = {
            "atomic:operations": operations
        }

        expected_result = {
            "atomic:results": [
                {
                    "data": {
                        "id": "1",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        }
                    }
                },
                {
                    "data": {
                        "id": "1",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed2!"
                        }
                    }
                }
            ]
        }

        response = self.client.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',

            **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
        )

        self.assertEqual(0, BasicModel.objects.count())

        self.assertDictEqual(expected_result,
                             json.loads(response.content))

    def test_parser_exception_with_pointer(self):
        operations = [
            {
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "update",
                "data": {
                    "id": "1",
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed2!"
                    }
                }
            }, {
                "op": "remove",
                "ref": {
                    # "id": "1",
                    "type": "BasicModel",
                }
            }
        ]

        data = {
            "atomic:operations": operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',

            **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
        )
        error = json.loads(response.content)
        expected_error = {
            "errors": [
                {
                    "id": "missing-id",
                    "detail": "The resource identifier object must contain an `id` member",
                    "status": "400",
                    "source": {
                        "pointer": "/atomic:operations/2/ref"
                    },
                }
            ]
        }
        self.assertEqual(400, response.status_code)
        self.assertDictEqual(expected_error, error)

    def test_view_422_response(self):
        operations = [
            {
                "op": "update",
                "data": {
                    "id": "1",
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed2!"
                    }
                }
            }
        ]

        data = {
            "atomic:operations": operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',

            **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
        )
        error = json.loads(response.content)
        expected_error = {
            "errors": [
                {
                    "id": "object-does-not-exist",
                    "detail": "Object with id `1` received for operation with index `0` does not exist",
                    "status": "422",
                    "source": {
                        "pointer": "/atomic:operations/0/data/id"
                    },
                }
            ]
        }
        self.assertEqual(422, response.status_code)
        self.assertDictEqual(expected_error, error)

    def test_view_204_response(self):
        obj = BasicModel.objects.create()

        operations = [
            {
                "op": "remove",
                "ref": {
                    "id": obj.pk,
                    "type": "BasicModel"
                }
            }
        ]

        data = {
            "atomic:operations": operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',

            **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
        )

        self.assertEqual(204, response.status_code)
        self.assertFalse(response.content)
