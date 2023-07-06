from django.urls import path

from tests.views import BulkAtomicOperationView, ConcretAtomicOperationView


urlpatterns = [
    path("", ConcretAtomicOperationView.as_view()),
    path("bulk", BulkAtomicOperationView.as_view())

]
