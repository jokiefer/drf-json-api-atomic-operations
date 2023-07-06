"""
Parsers
"""
from typing import Dict

from rest_framework_json_api import renderers
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.utils import undo_format_field_name

from atomic_operations.consts import ATOMIC_CONTENT_TYPE, ATOMIC_OPERATIONS
from atomic_operations.exceptions import (
    InvalidPrimaryDataType,
    JsonApiParseError,
    MissingPrimaryData,
)


class AtomicOperationParser(JSONParser):
    """
    Similar to `JSONRenderer`, the `JSONParser` you may override the following methods if you
    need highly custom parsing control.

    A JSON:API client will send a payload that looks like this:

    .. code:: json

        {
            "atomic:operations": [{
                    "op": "add",
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

    media_type = ATOMIC_CONTENT_TYPE
    renderer_class = renderers.JSONRenderer

    def check_resource_identifier_object(self, idx: int, resource_identifier_object: Dict, operation_code: str):
        if operation_code in ["update", "remove"] and not resource_identifier_object.get("id"):
            raise JsonApiParseError(
                id="missing-id",
                detail="The resource identifier object must contain an `id` member",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/{'data' if operation_code == 'update' else 'ref'}"
            )
        if not resource_identifier_object.get("type"):
            raise JsonApiParseError(
                id="missing-type",
                detail="The resource identifier object must contain an `type` member",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/{'data' if operation_code == 'update' else 'ref'}"
            )

    def check_add_operation(self, idx, data):
        if not isinstance(data, dict):
            raise MissingPrimaryData(idx)
        self.check_resource_identifier_object(idx, data, "add")

    def check_relation_update(self, idx, operation):
        self.check_resource_identifier_object(idx, operation["ref"], "update")
        # relationship update detected
        relationship = operation["ref"].get("relationship")
        if not relationship:
            # relationship update must name the attribute
            raise JsonApiParseError(
                id="missing-relationship-naming",
                detail="relationship must be named by the `relationship` attribute",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/ref"
            )
        try:
            data = operation["data"]
            if data == None:
                # clear relation, this is valid
                return

            if not isinstance(data, (dict, list)):
                # relationship update data must be a dict (to-one) or list (to-many)
                # TODO: if we know the relation type, we could provide a more detailed error message
                raise InvalidPrimaryDataType(idx, "object or array")

            if isinstance(data, dict):
                self.check_resource_identifier_object(idx, data, "update")
            else:
                for relation in data:
                    self.check_resource_identifier_object(idx, relation, "update")

        except KeyError:
            # relationship update must provide data attribute. It could be None but it must be present.
            raise MissingPrimaryData(idx)

    def check_update_operation(self, idx, operation):
        ref = operation.get("ref")
        if ref:
            self.check_relation_update(idx, operation)
        else:
            data = operation.get("data")
            if not data:
                raise MissingPrimaryData(idx)
            elif not isinstance(data, dict):
                raise InvalidPrimaryDataType(idx, "object")

    def check_remove_operation(self, idx, ref):
        if not ref:
            raise JsonApiParseError(
                id="missing-ref-attribute",
                detail="`ref` must be part of remove operation",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}"
            )
        self.check_resource_identifier_object(idx, ref, "remove")

    def check_operation(self, idx: int, operation: Dict):
        operation_code: str = operation.get("op")
        ref: dict = operation.get("ref")
        href: str = operation.get("href")
        data = operation.get("data")

        if not operation_code:
            raise JsonApiParseError(
                id="missing-operation-code",
                detail="Received operation does not provide an operation code",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/op"
            )

        if href:
            # for now we do not support href's. This is optional by the standard (MAY) https://jsonapi.org/ext/atomic/#operation-objects
            raise JsonApiParseError(
                id="not-implemented",
                detail="Received operation using `href` to refencing objects which is not implemented by this api. Use `ref` instead.",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/href"
            )

        if operation_code == "add":
            self.check_add_operation(idx, data)

        elif operation_code == "remove":
            self.check_remove_operation(idx, ref)

        elif operation_code == "update":
            self.check_update_operation(idx, operation)
        else:
            raise JsonApiParseError(
                id="unknown-operation-code",
                detail=f"Unknown operation `{operation_code}` received",
                pointer=f"/{ATOMIC_OPERATIONS}/{idx}/op"
            )

    def parse_id_and_type(self, resource_identifier_object):
        parsed_data = {"id": resource_identifier_object.get(
            "id")} if "id" in resource_identifier_object else {}
        parsed_data["type"] = resource_identifier_object.get("type")
        return parsed_data

    def check_root(self, result):
        if not isinstance(result, dict) or ATOMIC_OPERATIONS not in result:
            raise JsonApiParseError(
                id="missing-operation-objects",
                detail="Received document does not contain operations objects",
                pointer=f"/{ATOMIC_OPERATIONS}"
            )

        # Sanity check
        if not isinstance(result.get(ATOMIC_OPERATIONS), list):
            raise JsonApiParseError(
                id="invalid-operation-objects",
                detail="Received operation objects is not a valid JSON:API atomic operation request",
                pointer=f"/{ATOMIC_OPERATIONS}"
            )

    def parse_operation(self, resource_identifier_object, result):
        _parsed_data = self.parse_id_and_type(resource_identifier_object)
        _parsed_data.update(self.parse_attributes(resource_identifier_object))
        _parsed_data.update(self.parse_relationships(resource_identifier_object))
        _parsed_data.update(self.parse_metadata(result))
        return _parsed_data

    def parse_data(self, result, parser_context):
        """
        Formats the output of calling JSONParser to match the JSON:API specification
        and returns the result.
        """
        self.check_root(result)

        # Construct the return data
        parsed_data = []
        for idx, operation in enumerate(result[ATOMIC_OPERATIONS]):

            self.check_operation(idx, operation)

            if operation["op"] == "update" and operation.get("ref"):
                # special case relation update
                ref: Dict = operation["ref"]
                ref["relationships"] = {
                    ref.pop("relationship"): {
                        "data": operation["data"]
                    }
                }
                _parsed_data = self.parse_operation(
                    resource_identifier_object=ref,
                    result=result
                )

                operation_code = f'{operation["op"]}-relationship'

            else:
                _parsed_data = self.parse_operation(
                    resource_identifier_object=operation.get(
                        "data", operation.get("ref")
                    ),
                    result=result
                )
                operation_code = operation["op"]

            parsed_data.append({
                operation_code: _parsed_data
            })

        return parsed_data
