from django.urls import path

from tests.views import ConcretAtomicOperationView

urlpatterns = [
    path("", ConcretAtomicOperationView.as_view())
]
