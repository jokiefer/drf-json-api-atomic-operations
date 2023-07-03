from typing import TypedDict

from rest_framework.serializers import Serializer


class SerializerMapping(TypedDict):
    type: str
    serializer: Serializer
