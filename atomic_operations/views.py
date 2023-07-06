from typing import Dict, List

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db.transaction import atomic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from atomic_operations.consts import ATOMIC_OPERATIONS
from atomic_operations.exceptions import UnprocessableEntity
from atomic_operations.parsers import AtomicOperationParser
from atomic_operations.renderers import AtomicResultRenderer


class AtomicOperationView(APIView):
    """View which handles JSON:API Atomic Operations extension https://jsonapi.org/ext/atomic/"""

    renderer_classes = [AtomicResultRenderer]
    parser_classes = [AtomicOperationParser]

    # only post method is allowed https://jsonapi.org/ext/atomic/#processing
    http_method_names = ["post"]

    #
    serializer_classes: Dict = {}

    sequential = True
    response_data: List[Dict] = []

    # TODO: proof how to check permissions for all operations
    # permission_classes = TODO
    # call def check_permissions for `add` operation
    # call def check_object_permissions for `update` and `remove` operation

    def get_serializer_classes(self) -> Dict:
        if self.serializer_classes:
            return self.serializer_classes
        else:
            raise ImproperlyConfigured("You need to define the serializer classes. "
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

    def get_serializer(self, idx, operation_code, resource_type, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class(
            operation_code, resource_type)
        kwargs.setdefault('context', self.get_serializer_context())

        if operation_code in ["update", "remove"]:
            try:
                kwargs.update({
                    "instance": serializer_class.Meta.model.objects.get(pk=kwargs["data"]["id"])
                })
            except ObjectDoesNotExist:
                raise UnprocessableEntity([
                    {
                        "id": "object-does-not-exist",
                        "detail": f'Object with id `{kwargs["data"]["id"]}` received for operation with index `{idx}` does not exist',
                        "source": {
                            "pointer": f"/{ATOMIC_OPERATIONS}/{idx}/data/id"
                        },
                        "status": "422"
                    }
                ]
                )

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

    def handle_sequential(self, serializer, operation_code):
        if operation_code in ["add", "update", "update-relationship"]:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if operation_code != "update-relationship":
                self.response_data.append(serializer.data)
        else:
            # remove
            serializer.instance.delete()

    def perform_bulk_create(self, bulk_operation_data):
        objs = []
        model_class = bulk_operation_data["serializer_collection"][0].Meta.model
        for _serializer in bulk_operation_data["serializer_collection"]:
            _serializer.is_valid(raise_exception=True)
            instance = model_class(**_serializer.validated_data)
            objs.append(instance)
            self.response_data.append(
                _serializer.__class__(instance=instance).data)
        model_class.objects.bulk_create(
            objs)

    def perform_bulk_delete(self, bulk_operation_data):
        obj_ids = []
        for _serializer in bulk_operation_data["serializer_collection"]:
            obj_ids.append(_serializer.instance.pk)
            self.response_data.append(_serializer.data)
        bulk_operation_data["serializer_collection"][0].Meta.model.objects.filter(
            pk__in=obj_ids).delete()

    def handle_bulk(self, serializer, current_operation_code, bulk_operation_data):
        bulk_operation_data["serializer_collection"].append(serializer)
        if bulk_operation_data["next_operation_code"] != current_operation_code or bulk_operation_data["next_resource_type"] != serializer.initial_data["type"]:
            if current_operation_code == "add":
                self.perform_bulk_create(bulk_operation_data)
            elif current_operation_code == "delete":
                self.perform_bulk_delete(bulk_operation_data)
            else:
                # TODO: update in bulk requires more logic cause it could be a partial update and every field differs pers instance.
                # Then we can't do a bulk operation. This is only possible for instances which changes the same field(s).
                # Maybe the anylsis of this takes longer than simple handling updates in sequential mode.
                # For now we handle updates always in sequential mode
                self.handle_sequential(
                    bulk_operation_data["serializer_collection"][0], current_operation_code)
            bulk_operation_data["serializer_collection"] = []

    def perform_operations(self, parsed_operations: List[Dict]):
        self.response_data = []  # reset local response data storage

        bulk_operation_data = {
            "serializer_collection": [],
            "next_operation_code": "",
            "next_resource_type": ""
        }

        with atomic():

            for idx, operation in enumerate(parsed_operations):
                operation_code = next(iter(operation))
                obj = operation[operation_code]

                serializer = self.get_serializer(
                    idx=idx,
                    data=obj,
                    operation_code="update" if operation_code == "update-relationship" else operation_code,
                    resource_type=obj["type"],
                    partial=True if "update" in operation_code else False
                )

                if self.sequential:
                    self.handle_sequential(serializer, operation_code)
                else:
                    is_last_iter = parsed_operations.__len__() == idx + 1
                    if is_last_iter:
                        bulk_operation_data["next_operation_code"] = ""
                        bulk_operation_data["next_resource_type"] = ""
                    else:
                        next_operation = parsed_operations[idx + 1]
                        bulk_operation_data["next_operation_code"] = next(
                            iter(next_operation))
                        bulk_operation_data["next_resource_type"] = next_operation[bulk_operation_data["next_operation_code"]]["type"]

                    self.handle_bulk(
                        serializer=serializer,
                        current_operation_code=operation_code,
                        bulk_operation_data=bulk_operation_data
                    )

        return Response(self.response_data, status=status.HTTP_200_OK if self.response_data else status.HTTP_204_NO_CONTENT)
