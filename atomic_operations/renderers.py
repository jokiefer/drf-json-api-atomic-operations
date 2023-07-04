"""
Renderers
"""
import json
from typing import List, OrderedDict

from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api.utils import get_resource_type_from_serializer


class AtomicResultRenderer(JSONRenderer):
    """
    The `JSONRenderer` exposes a number of methods that you may override if you need highly
    custom rendering control.

    Render a JSON response per the JSON:API spec:

    .. code-block:: json

        {
          "atomic:results": [{
            "data": {
              "links": {
                "self": "http://example.com/blogPosts/13"
              },
              "type": "articles",
              "id": "13",
              "attributes": {
                "title": "JSON API paints my bikeshed!"
              }
            }
          }]
        }
    """

    media_type = 'application/vnd.api+json;ext="https://jsonapi.org/ext/atomic'
    format = 'vnd.api+json;ext="https://jsonapi.org/ext/atomic'

    def check_error(self, operation_result_data, accepted_media_type, renderer_context):
        # primitive check if any operation has errors while parsing
        status = operation_result_data.get("status")
        try:
            status = int(status)
            if status >= 400 and status <= 600:
                return self.render_errors([operation_result_data], accepted_media_type, renderer_context)
        except Exception:
            pass

    def render(self, data: List[OrderedDict], accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {"view": {}}

        atomic_results = []
        for operation_result_data in data:
            has_error = self.check_error(
                operation_result_data, accepted_media_type, renderer_context)
            if has_error:
                return has_error

            # pass in the resource name
            renderer_context["view"].resource_name = get_resource_type_from_serializer(
                operation_result_data.serializer)
            rendered_primary_data = super().render(
                operation_result_data, accepted_media_type, renderer_context)
            atomic_results.append(rendered_primary_data.decode("UTF-8"))

        atomic_results_str = f"[{','.join(atomic_results)}]"

        rendered_content = '{"atomic:results":' + atomic_results_str + '}'

        return rendered_content.encode()
