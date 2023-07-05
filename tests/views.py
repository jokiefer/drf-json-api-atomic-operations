from atomic_operations.views import AtomicOperationView
from tests.serializers import (
    BasicModelSerializer,
    RelatedModelSerializer,
    RelatedModelTwoSerializer,
)


class ConcretAtomicOperationView(AtomicOperationView):
    serializer_classes = {
        "add:BasicModel": BasicModelSerializer,
        "update:BasicModel": BasicModelSerializer,
        "remove:BasicModel": BasicModelSerializer,
        "add:RelatedModel": RelatedModelSerializer,
        "add:RelatedModelTwo": RelatedModelTwoSerializer,
    }
