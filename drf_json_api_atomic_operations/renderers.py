"""
Renderers
"""
import copy
from collections import defaultdict
from collections.abc import Iterable
from typing import List, OrderedDict

import inflection
import rest_framework_json_api
from django.db.models import Manager
from django.template import loader
from django.utils.encoding import force_str
from rest_framework.fields import SkipField, get_attribute
from rest_framework.relations import PKOnlyObject
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework_json_api import utils
from rest_framework_json_api.relations import (
    HyperlinkedMixin, ManySerializerMethodResourceRelatedField,
    ResourceRelatedField, SkipDataMixin)
from rest_framework_json_api.renderers import JSONRenderer


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

    def render(self, data: List[OrderedDict], accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {"view": {}}

        atomic_results = []
        for operation_result_data in data:
            # pass in the resource name
            renderer_context["view"]["resource_name"] = operation_result_data["type"]
            atomic_results.append(super().render(
                operation_result_data, accepted_media_type, renderer_context))
        return {
            "atomic:results": atomic_results
        }
