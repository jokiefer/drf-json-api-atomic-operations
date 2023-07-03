"""
Parsers
"""
from typing import Dict, List

from rest_framework.exceptions import ParseError
# from rest_framework.parsers import JSONParser
from rest_framework_json_api import exceptions, renderers
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.utils import get_resource_type_from_serializer


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

        if op == "remove":
            # check reference object object: https://jsonapi.org/ext/atomic/#auto-id-deleting-resources
            ref = operation.get("ref")
            href = operation.get("href")

            if ref and href:
                raise ParseError(
                    "using ref and href at the same time is not allowed.")
            elif not ref and not href:
                raise ParseError(
                    "either ref or href must be part of the remove operation")

    def check_primary_data(self, operation: Dict, parser_context):
        data = operation.get("data")
        op = operation.get("op", None)

        # Sanity check
        if not isinstance(data, dict):
            raise ParseError(
                "Received data is not a valid JSON:API Resource Identifier Object"
            )

        if not data.get("id") and op in ("update", "remove"):
            raise ParseError(
                "The resource identifier object must contain an 'id' member"
            )

    def parse_id_and_type(self, data):
        parsed_data = {"id": data.get("id")} if "id" in data else {}
        parsed_data["type"] = data.get("type")
        return parsed_data

    def parse_data(self, result, parser_context):
        """
        Formats the output of calling JSONParser to match the JSON:API specification
        and returns the result.
        """
        if not isinstance(result, dict) or "atomic:operations" not in result:
            raise ParseError(
                "Received document does not contain operations object data")

        operations = result.get("atomic:operations")

        # Sanity check
        if not isinstance(operations, list):
            raise ParseError(
                "Received operations is not a valid JSON:API atomic operation request"
            )

        # Construct the return data
        parsed_data = []
        for idx, operation in enumerate(operations):
            self.check_operation_code(idx, operation)
            self.check_primary_data(operation, parser_context)
            data = operation["data"]
            op = operation["op"]

            if op == "remove":
                _parsed_data = self.parse_id_and_type(data=data["ref"])
            else:
                _parsed_data = self.parse_id_and_type(data=data)
                _parsed_data.update(self.parse_attributes(data))
                _parsed_data.update(self.parse_relationships(data))
                _parsed_data.update(self.parse_metadata(result))
            parsed_data.append({
                operation.get("op"): _parsed_data
            })

        return parsed_data
