from rest_framework_json_api.serializers import ModelSerializer

from tests.models import BasicModel


class BasicModelSerializer(ModelSerializer):
    class Meta:
        fields = ("text",)
        model = BasicModel
