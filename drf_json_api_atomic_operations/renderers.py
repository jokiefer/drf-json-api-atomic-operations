"""
Renderers
"""
import copy
from collections import defaultdict
from collections.abc import Iterable

import inflection
import rest_framework_json_api
from django.db.models import Manager
from django.template import loader
from django.utils.encoding import force_str
from rest_framework.fields import SkipField, get_attribute
from rest_framework.relations import PKOnlyObject
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import ListSerializer, Serializer
from rest_framework.settings import api_settings
from rest_framework_json_api import utils
from rest_framework_json_api.relations import (
    HyperlinkedMixin, ManySerializerMethodResourceRelatedField,
    ResourceRelatedField, SkipDataMixin)


class AtomicResultRenderer(JSONRenderer):
    """
    The `JSONRenderer` exposes a number of methods that you may override if you need highly
    custom rendering control.

    Render a JSON response per the JSON:API spec:

    .. code-block:: json

        {
          "data": [
            {
              "type": "companies",
              "id": "1",
              "attributes": {
                "name": "Mozilla",
                "slug": "mozilla",
                "date-created": "2014-03-13 16:33:37"
              }
            }
          ]
        }
    """

    media_type = "application/vnd.api+json"
    format = "vnd.api+json"
