"""
Parsers
"""
from typing import Dict, List

from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework_json_api import exceptions, renderers
from rest_framework_json_api.utils import (get_resource_name,
                                           undo_format_field_names)


class AtomicOperationParser(JSONParser):
    """
    Similar to `JSONRenderer`, the `JSONParser` you may override the following methods if you
    need highly custom parsing control.

    A JSON:API client will send a payload that looks like this:

    .. code:: json

        {
            "atomic:operations": [{
                    "op": "add",
                    "href": "/blogPosts",
                    "data": {
                    "type": "articles",
                    "attributes": {
                        "title": "JSON API paints my bikeshed!"
                    }
                    }
                }]
        }

    We extract the attributes so that DRF serializers can work as normal.
    """

    media_type = 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'
    renderer_class = renderers.JSONRenderer

    def check_operation_code(self, idx: int, operation: Dict):
        op = operation.get("op", None)
        if not op:
            raise ParseError(
                f"Received operation with index {idx} does not provide an operation code.")
        if op not in ["add", "update", "remove"]:
            raise ParseError(
                f"Unknown operation `{op}` received for operation with index {idx}")



    def parse_data(self, result, parser_context) -> List[]:
        """
        Formats the output of calling JSONParser to match the JSON:API specification
        and returns the result.
        """
        if not isinstance(result, dict) or "atomic:operations" not in result:
            raise ParseError(
                "Received document does not contain operations object data")

        operations = result.get("atomic:operations")
        parser_context = parser_context or {}
        view = parser_context.get("view")

        # Sanity check
        if not isinstance(operations, list):
            raise ParseError(
                "Received operations is not a valid JSON:API atomic operation request"
            )

        

        for idx, operation in enumerate(operations):
            self.check_operation_code(idx, operation)
            # TODO: pre check if operation primary data is correct
            serializer = view.get_serializer_class(operation, operation["data"]["type"])

        # TODO: parse every operation object... otherwise it can't be processed with our serializers



        
        # Construct the return data
        parsed_data = {"id": data.get("id")} if "id" in data else {}
        parsed_data["type"] = data.get("type")
        parsed_data.update(self.parse_attributes(data))
        parsed_data.update(self.parse_relationships(data))
        parsed_data.update(self.parse_metadata(result))
        return parsed_data

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data
        """
        result = super().parse(
            stream, media_type=media_type, parser_context=parser_context
        )

        return self.parse_data(result, parser_context)
