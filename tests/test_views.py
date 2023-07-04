import json

from django.test import Client, RequestFactory, TestCase

from tests.models import BasicModel
from tests.views import ConcretAtomicOperationView


class TestAtomicOperationView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ConcretAtomicOperationView
        self.client = Client()

    def test_view(self):
        data = {
            "atomic:operations": [
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
                }
            ]
        }
        post_request = self.factory.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json;ext="https://jsonapi.org/ext/atomic',
            **{"HTTP_ACCEPT": 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'}
        )
        response = self.view.as_view()(post_request)

    def test_view_two(self):

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
