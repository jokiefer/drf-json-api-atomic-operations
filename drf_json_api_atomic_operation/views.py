from parsers import AtomicOperationParser
from renderers import AtomicResultRenderer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class AtomicOperationView(APIView):
    renderer_classes = AtomicResultRenderer
    parser_classes = AtomicOperationParser

    # only post method is allowed https://jsonapi.org/ext/atomic/#processing
    http_method_names = ["post"]

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
