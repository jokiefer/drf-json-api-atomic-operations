from typing import Dict, List

from django.core.exceptions import ImproperlyConfigured
from parsers import AtomicOperationParser
from renderers import AtomicResultRenderer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_json_api_atomic_operation.types import SerializerMapping


class AtomicOperationView(APIView):
    renderer_classes = AtomicResultRenderer
    parser_classes = AtomicOperationParser

    # only post method is allowed https://jsonapi.org/ext/atomic/#processing
    http_method_names = ["post"]

    serializer_classes: Dict = {}

    def get_serializer_classes(self) -> Dict:
        if self.serializer_classes:
            return self.serializer_classes
        else:
            raise ImproperlyConfigured(f"You need to define the serializer classes. "
                                       "Otherwise serialization of json:api primary data is not possible.")

    def get_serializer_class(self, operation: str, type: str):
        serializer_class = self.get_serializer_classes().get(
            f"{operation}:{type}")
        if serializer_class:
            return serializer_class
        else:
            # TODO: is this error message correct? Check jsonapi spec for this
            raise ImproperlyConfigured(
                f"No serializer for type `{type}` and operation `{operation}` where found")

    # TODO: proof how to check permissions for all operations
    # permission_classes = TODO
    # call def check_permissions for `add` operation
    # call def check_object_permissions for `update` and `remove` operation

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def post(self, request, *args, **kwargs):
        request.data  # this is the data returned from the json parser

        # TODO: serialize every operation data with the correct serializer

        return self.create(request, *args, **kwargs)
