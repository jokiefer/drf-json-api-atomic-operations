import json
from io import BytesIO

from django.test import Client, RequestFactory, TestCase

from tests.views import ConcretAtomicOperationView


class TestAtomicOperationView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ConcretAtomicOperationView

    def test_parse(self):
        data = {
            "atomic:operations": [
                {
                    "op": "add",
                    "href": "/blogPosts",
                    "data": {
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
                    "op": "update",
                    "href": "/blogPosts",
                    "data": {
                        "id": "1",
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
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

        i = 0
