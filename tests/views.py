from atomic_operations.views import AtomicOperationView
from tests.serializers import BasicModelSerializer


class ConcretAtomicOperationView(AtomicOperationView):
    serializer_classes = {
        "add:BasicModel": BasicModelSerializer,
        "update:BasicModel": BasicModelSerializer,
        "remove:BasicModel": BasicModelSerializer,
    }
