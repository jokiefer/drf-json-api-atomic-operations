import json
from io import BytesIO

from django.test import RequestFactory, TestCase

from drf_json_api_atomic_operations.parsers import AtomicOperationParser
from tests.views import ConcretAtomicOperationView


class TestAtomicOperationParser(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.parser = AtomicOperationParser()
        self.parser_context = {"request": self.factory.post(
            "/"), "kwargs": {}, "view": ConcretAtomicOperationView()}

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
        stream = BytesIO(json.dumps(data).encode("utf-8"))

        result = self.parser.parse(stream, parser_context=self.parser_context)

        expected_result = [
            {
                "add": {
                    "type": "articles",
                    "title": "JSON API paints my bikeshed!"
                }
            },
            {
                "update": {
                    "id": "1",
                    "type": "articles",
                    "title": "JSON API paints my bikeshed!"
                }
            }
        ]
        self.assertEqual(expected_result, result)
