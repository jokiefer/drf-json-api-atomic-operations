import json
from io import BytesIO

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ParseError

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
                }, {
                    "op": "remove",
                    "ref": {
                        "id": "1",
                        "type": "articles",
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
            },
            {
                "remove": {
                    "id": "1",
                    "type": "articles",
                }
            }
        ]
        self.assertEqual(expected_result, result)

    def test_unsupported_operation_code(self):
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
                    "op": "unknown",
                    "href": "/blogPosts",
                    "data": {
                        "id": "1",
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
                    "op": "remove",
                    "ref": {
                        "id": "1",
                        "type": "articles",
                    }
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "Unknown operation `unknown` received for operation with index 1",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_missing_operation_code(self):
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
                    "href": "/blogPosts",
                    "data": {
                        "id": "1",
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
                    "op": "remove",
                    "ref": {
                        "id": "1",
                        "type": "articles",
                    }
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "Received operation with index 1 does not provide an operation code",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_missing_ref_href_on_remove(self):
        data = {
            "atomic:operations": [
                {
                    "op": "remove",

                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "either ref or href must be part of the remove operation with index 0",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_using_ref_href_together_on_remove(self):
        data = {
            "atomic:operations": [
                {
                    "op": "remove",
                    "href": "/somearticle",
                    "ref": {
                        "id": "1",
                        "type": "articles",
                    }
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "using ref and href together on operation with index 0 is not allowed",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_primary_data_without_id(self):
        data = {
            "atomic:operations": [
                {
                    "op": "remove",
                    "ref": {
                        "type": "articles",
                    }
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "The resource identifier object with index 0 must contain an 'id' member",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = {
            "atomic:operations": [
                {
                    "op": "update",
                    "ref": {
                        "type": "articles",
                    }
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "The resource identifier object with index 0 must contain an 'id' member",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_primary_data(self):
        data = {
            "atomic:operations": [
                {
                    "op": "update",
                    "id": "1",
                    "data": []
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "Received data of operation with index 0 is not a valid JSON:API Resource Identifier Object",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_is_atomic_operations(self):
        data = {
            "atomic:operation": [
                {
                    "op": "update",
                    "id": "1",
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
        self.assertRaisesRegex(
            ParseError,
            "Received document does not contain operations object data",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = []
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "Received document does not contain operations object data",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = {
            "atomic:operations": {}
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            ParseError,
            "Received operations is not a valid JSON:API atomic operation request",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )
