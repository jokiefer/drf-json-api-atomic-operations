import json

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
    #         content_type=ATOMIC_MEDIA_TYPE,
    #         **{"HTTP_ACCEPT": ATOMIC_MEDIA_TYPE}
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

            # {
            #     "op": "update",
            #     "ref": {
            #         "id": "2",
            #         "type": "BasicModel",
            #         "relationship": "to_one"
            #     },
            #     "data": {"type": "RelatedModel", "id": "1"}
            # }, {
            #     "op": "update",
            #     "ref": {
            #         "id": "2",
            #         "type": "BasicModel",
            #         "relationship": "to_many"
            #     },
            #     "data": [{"type": "RelatedModelTwo", "id": "1"}, {"type": "RelatedModelTwo", "id": "2"}]
            # }
        ]

        data = {
            ATOMIC_OPERATIONS: operations
        }

        expected_result = {
            ATOMIC_RESULTS: [
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
                        "id": "2",
                        "type": "BasicModel",
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
                        }
                    }
                },
            ]
        }

        response = self.client.post(
            path="/",
            data=data,
            content_type=ATOMIC_CONTENT_TYPE,

            **{"HTTP_ACCEPT": ATOMIC_CONTENT_TYPE}
        )

        self.assertEqual(1, BasicModel.objects.count())
        self.assertEqual(1, RelatedModel.objects.count())
        self.assertEqual(2, RelatedModelTwo.objects.count())

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
