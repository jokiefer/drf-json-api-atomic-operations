"""
Parsers
"""
from typing import Dict

from rest_framework.exceptions import ParseError
from rest_framework_json_api import renderers
from rest_framework_json_api.parsers import JSONParser


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
            raise ParseError([
                {
                    "id": "missing-operation-code",
                    "detail": f"Received operation with index {idx} does not provide an operation code",
                    "source": {
                        "pointer": f"/atomic:operations[{idx}]/op"
                    },
                    "status": "400"
                }]
            )
        if op not in ["add", "update", "remove"]:
            raise ParseError([
                {
                    "id": "unknown-operation-code",
                    "detail": f"Unknown operation `{op}` received for operation with index {idx}",
                    "source": {
                        "pointer": f"/atomic:operations[{idx}]/op"
                    },
                    "status": "400"
                }]
            )

        if op == "remove":
            # check reference object object: https://jsonapi.org/ext/atomic/#auto-id-deleting-resources
            ref = operation.get("ref")
            href = operation.get("href")

            if ref and href:
                raise ParseError(
                    [
                        {
                            "id": "ref-href-together",
                            "detail": f"using ref and href together on operation with index {idx} is not allowed.",
                            "source": {
                                "pointer": f"/atomic:operations[{idx}]/href"
                            },
                            "status": "400"
                        }]
                )
            elif not ref and not href:
                raise ParseError(
                    [
                        {
                            "id": "missing-ref-or-href",
                            "detail": f"either ref or href must be part of the remove operation with index {idx}",
                            "source": {
                                "pointer": f"/atomic:operations[{idx}]"
                            },
                            "status": "400"
                        }]
                )

    def check_primary_data(self, idx: int, data: Dict, operation_code: str):
        # Sanity check
        if not isinstance(data, dict):
            raise ParseError([
                {
                    "id": "invalid-operation-object",
                    "detail": f"Received data of operation with index {idx} is not a valid JSON:API Operation Object",
                    "source": {
                        "pointer": f"/atomic:operations[{idx}]"
                    },
                    "status": "400"
                }]
            )

        if not data.get("id") and operation_code in ("update", "remove"):
            raise ParseError(
                [
                    {
                        "id": "missing-id",
                        "detail": f"The resource identifier object with index {idx} must contain an `id` member",
                        "source": {
                            "pointer": f"/atomic:operations[{idx}]/id"
                        },
                        "status": "400"
                    }]
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
                [
                    {
                        "id": "missing-operation-objects",
                        "detail": "Received document does not contain operations objects",
                        "source": {
                            "pointer": "/atomic:operations/"
                        },
                        "status": "400"
                    }]
            )

        operations = result.get("atomic:operations")

        # Sanity check
        if not isinstance(operations, list):
            raise ParseError(
                [
                    {
                        "id": "invalid-operation-objects",
                        "detail": "Received operation objects is not a valid JSON:API atomic operation request",
                        "source": {
                            "pointer": "/atomic:operations/"
                        },
                        "status": "400"
                    }]
            )

        # Construct the return data
        parsed_data = []
        for idx, operation in enumerate(operations):
            self.check_operation_code(idx, operation)
            data = operation.get("data", operation.get(
                "ref", operation.get("href")))
            operation_code = operation["op"]
            self.check_primary_data(idx, data, operation_code)

            _parsed_data = self.parse_id_and_type(data=data)
            _parsed_data.update(self.parse_attributes(data))
            _parsed_data.update(self.parse_relationships(data))
            _parsed_data.update(self.parse_metadata(result))
            parsed_data.append({
                operation_code: _parsed_data
            })

        return parsed_data
