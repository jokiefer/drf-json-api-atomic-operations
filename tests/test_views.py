import json

from django import VERSION
from django.test import Client, RequestFactory, TestCase

from atomic_operations.consts import (
    ATOMIC_CONTENT_TYPE,
    ATOMIC_OPERATIONS,
    ATOMIC_RESULTS,
)
from tests.models import BasicModel, RelatedModel, RelatedModelTwo
from tests.views import ConcretAtomicOperationView


class TestAtomicOperationView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = ConcretAtomicOperationView
        self.client = Client()

        self.maxDiff = None

    def test_content_type_extension(self):
        """Test that the correct content type is accepted
        
        The media type and parameters are defined at https://jsonapi.org/ext/atomic. This tests
        hardcodes the value to separate the test from the library's constants.
        
        """
        operations = []

        data = {
            ATOMIC_OPERATIONS: operations
        }

        response = self.client.post(
            path="/",
            data=data,
            content_type='application/vnd.api+json; ext="https://jsonapi.org/ext/atomic"',

            **{"HTTP_ACCEPT": 'application/vnd.api+json; ext="https://jsonapi.org/ext/atomic"'}
        )

        self.assertNotEqual(406, response.status_code)  # 406 Not Acceptable

    def test_view_processing_with_valid_request(self):
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
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "RelatedModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "RelatedModelTwo",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "RelatedModelTwo",
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
            },
            {
                "op": "update",
                "ref": {
                    "id": "2",
                    "type": "BasicModel",
                    "relationship": "to_one"
                },
                "data": {"type": "RelatedModel", "id": "1"}
            }, {
                "op": "update",
                "ref": {
                    "id": "2",
                    "type": "BasicModel",
                    "relationship": "to_many"
                },
                "data": [{"type": "RelatedModelTwo", "id": "1"}, {"type": "RelatedModelTwo", "id": "2"}]
            }
        ]

        data = {
            ATOMIC_OPERATIONS: operations
        }

        response = self.client.post(
            path="/",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )

        # check response
        self.assertEqual(200, response.status_code)

        expected_result = {
            ATOMIC_RESULTS: [
                {
                    "data": {
                        "id": "1",

                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                },
                {
                    "data": {
                        "id": "2",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                },
                {
                    "data": {
                        "id": "1",
                        "type": "RelatedModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        }
                    }
                },
                {
                    "data": {
                        "id": "1",
                        "type": "RelatedModelTwo",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        }
                    }
                },
                {
                    "data": {
                        "id": "2",
                        "type": "RelatedModelTwo",
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
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }

                    }
                },
            ]
        }

        self.assertDictEqual(expected_result,
                             json.loads(response.content))

        # check db content
        self.assertEqual(1, BasicModel.objects.count())
        self.assertEqual(1, RelatedModel.objects.count())
        self.assertEqual(2, RelatedModelTwo.objects.count())

        self.assertEqual(RelatedModel.objects.get(pk=1),
                         BasicModel.objects.get(pk=2).to_one)

        major, minor, _, _, _ = VERSION
        if int(major) <= 4 and int(minor) <= 1:
            self.assertQuerysetEqual(RelatedModelTwo.objects.filter(pk__in=[1, 2]),
                                     BasicModel.objects.get(pk=2).to_many.all())
        else:
            # with django 4.2 TransactionTestCase.assertQuerysetEqual() is deprecated in favor of assertQuerySetEqual().
            self.assertQuerySetEqual(RelatedModelTwo.objects.filter(pk__in=[1, 2]),
                                     BasicModel.objects.get(pk=2).to_many.all())

    def test_bulk_view_processing_with_valid_request(self):
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
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "BasicModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "add",
                "data": {
                    "type": "RelatedModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!"
                    }
                }
            }, {
                "op": "update",
                "data": {
                    "id": "1",
                    "type": "RelatedModel",
                    "attributes": {
                            "text": "JSON API paints my bikeshed!2"
                    }
                }
            }
        ]

        data = {
            ATOMIC_OPERATIONS: operations
        }

        response = self.client.post(
            path="/bulk",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )

        # check response
        self.assertEqual(200, response.status_code)

        expected_result = {
            ATOMIC_RESULTS: [
                {
                    "data": {
                        "id": "1",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                },
                {
                    "data": {
                        "id": "2",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                }, {
                    "data": {
                        "id": "3",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                },
                {
                    "data": {
                        "id": "4",
                        "type": "BasicModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        },
                        "relationships": {
                            "to_many": {'data': [], 'meta': {'count': 0}},
                            "to_one": {'data': None},
                        }
                    }
                },
                {
                    "data": {
                        "id": "1",
                        "type": "RelatedModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!"
                        }
                    }
                },
                {
                    "data": {
                        "id": "1",
                        "type": "RelatedModel",
                        "attributes": {
                            "text": "JSON API paints my bikeshed!2"
                        }
                    }
                }
            ]
        }

        self.assertDictEqual(expected_result,
                             json.loads(response.content))

        # check db content
        self.assertEqual(4, BasicModel.objects.count())

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
            ATOMIC_OPERATIONS: operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )
        error = json.loads(response.content)
        expected_error = {
            "errors": [
                {
                    "id": "missing-id",
                    "detail": "The resource identifier object must contain an `id` member",
                    "status": "400",
                    "source": {
                        "pointer": f"/{ATOMIC_OPERATIONS}/2/ref"
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
            ATOMIC_OPERATIONS: operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )
        error = json.loads(response.content)
        expected_error = {
            "errors": [
                {
                    "id": "object-does-not-exist",
                    "detail": "Object with id `1` received for operation with index `0` does not exist",
                    "status": "422",
                    "source": {
                        "pointer": f"/{ATOMIC_OPERATIONS}/0/data/id"
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
            ATOMIC_OPERATIONS: operations
        }
        response = self.client.post(
            path="/",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )

        self.assertEqual(204, response.status_code)
        self.assertFalse(response.content)
