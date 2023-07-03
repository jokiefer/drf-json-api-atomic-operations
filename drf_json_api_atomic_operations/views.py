from typing import Dict, List, OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.db.transaction import atomic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_json_api.views import ModelViewSet

from drf_json_api_atomic_operations.parsers import AtomicOperationParser
from drf_json_api_atomic_operations.renderers import AtomicResultRenderer
from drf_json_api_atomic_operations.types import SerializerMapping


class AtomicOperationView(APIView):
    renderer_classes = [AtomicResultRenderer]
    parser_classes = [AtomicOperationParser]

    # only post method is allowed https://jsonapi.org/ext/atomic/#processing
    http_method_names = ["post"]

    serializer_classes: Dict = {}

    # TODO: proof how to check permissions for all operations
    # permission_classes = TODO
    # call def check_permissions for `add` operation
    # call def check_object_permissions for `update` and `remove` operation

    def get_serializer_classes(self) -> Dict:
        if self.serializer_classes:
            return self.serializer_classes
        else:
            raise ImproperlyConfigured(f"You need to define the serializer classes. "
                                       "Otherwise serialization of json:api primary data is not possible.")

    def get_serializer_class(self, operation_code: str, resource_type: str):
        serializer_class = self.get_serializer_classes().get(
            f"{operation_code}:{resource_type}")
        if serializer_class:
            return serializer_class
        else:
            # TODO: is this error message correct? Check jsonapi spec for this
            raise ImproperlyConfigured(
                f"No serializer for type `{resource_type}` and operation `{operation_code}` where found")

    def get_serializer(self, operation_code, resource_type, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class(
            operation_code, resource_type)
        kwargs.setdefault('context', self.get_serializer_context())

        if operation_code == "update":
            kwargs.update({
                "instance": serializer_class.Meta.model.objects.get(pk=kwargs["data"]["id"])
            })

        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def post(self, request, *args, **kwargs):
        return self.perform_operations(request.data)

    def perform_operations(self, parsed_operations: List[Dict]):
        response_data: List[Dict] = []
        with atomic():
            for operation in parsed_operations:
                op_code = next(iter(operation))
                obj = operation[op_code]
                # TODO: collect operations of same op_code and resource type to support bulk_create | bulk_update | filter(id__in=[1,2,3]).delete()
                if op_code in ["add", "update"]:
                    serializer = self.get_serializer(
                        data=obj,
                        operation_code=op_code,
                        resource_type=obj["type"]
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    response_data.append(serializer.data)
                else:
                    # remove
                    instance = self.get_object()
                    instance.delete()

        return Response(response_data, status=status.HTTP_200_OK if response_data else status.HTTP_204_NO_CONTENT)
