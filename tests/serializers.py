from rest_framework_json_api.serializers import ModelSerializer

from tests.models import BasicModel, RelatedModel, RelatedModelTwo


class BasicModelSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = BasicModel


class RelatedModelSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RelatedModel


class RelatedModelTwoSerializer(ModelSerializer):
    class Meta:
        fields = "__all__"
        model = RelatedModelTwo
