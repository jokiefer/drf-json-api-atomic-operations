import json
from io import BytesIO

from django.test import RequestFactory, TestCase

from atomic_operations.consts import ATOMIC_OPERATIONS
from atomic_operations.exceptions import JsonApiParseError
from atomic_operations.parsers import AtomicOperationParser
from tests.views import ConcretAtomicOperationView


class TestAtomicOperationParser(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.parser = AtomicOperationParser()
        self.parser_context = {"request": self.factory.post(
            "/"), "kwargs": {}, "view": ConcretAtomicOperationView()}
        self.maxDiff = None

    def test_parse(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "add",
                    "data": {
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
                    "op": "update",
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
                }, {
                    "op": "update",
                    "ref": {
                        "type": "articles",
                        "id": "13",
                        "relationship": "author"
                    },
                    "data": {
                        "type": "people",
                        "id": "9"
                    }
                }, {
                    "op": "update",
                    "ref": {
                        "type": "articles",
                        "id": "13",
                        "relationship": "tags"
                    },
                    "data": [
                        {"type": "tags", "id": "2"},
                        {"type": "tags", "id": "3"}
                    ]
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
            }, {
                "update-relationship": {
                    "id": "13",
                    "type": "articles",
                    "author": {"type": "people", "id": "9"}
                }
            }, {
                "update-relationship": {
                    "id": "13",
                    "type": "articles",
                    "tags": [{'type': 'tags', 'id': '2'}, {'type': 'tags', 'id': '3'}]
                }
            }
        ]
        self.assertEqual(expected_result, result)

    def test_unsupported_operation_code(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "add",
                    "data": {
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
                    "op": "unknown",
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
            JsonApiParseError,
            "Unknown operation `unknown` received",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_missing_operation_code(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "add",
                    "data": {
                        "type": "articles",
                        "attributes": {
                            "title": "JSON API paints my bikeshed!"
                        }
                    }
                }, {
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
            JsonApiParseError,
            "Received operation does not provide an operation code",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_missing_ref_on_remove(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "remove",

                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            JsonApiParseError,
            "`ref` must be part of remove operation",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_using_href(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "remove",
                    "href": "/somearticle",

                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            JsonApiParseError,
            "Received operation using `href` to refencing objects which is not implemented by this api. Use `ref` instead.",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_primary_data_without_id(self):
        data = {
            ATOMIC_OPERATIONS: [
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
            JsonApiParseError,
            "The resource identifier object must contain an `id` member",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = {
            ATOMIC_OPERATIONS: [
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
            JsonApiParseError,
            "The resource identifier object must contain an `id` member",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

    def test_primary_data(self):
        data = {
            ATOMIC_OPERATIONS: [
                {
                    "op": "update",
                    "id": "1",
                    "data": []
                }
            ]
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            JsonApiParseError,
            "primary data object musst be present",
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
            JsonApiParseError,
            "Received document does not contain operations objects",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = []
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            JsonApiParseError,
            "Received document does not contain operations objects",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )

        data = {
            ATOMIC_OPERATIONS: {}
        }
        stream = BytesIO(json.dumps(data).encode("utf-8"))
        self.assertRaisesRegex(
            JsonApiParseError,
            "Received operation objects is not a valid JSON:API atomic operation request",
            self.parser.parse,
            **{
                "stream": stream,
                "parser_context": self.parser_context
            }
        )
