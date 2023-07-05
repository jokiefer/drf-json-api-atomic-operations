from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, ParseError


class UnprocessableEntity(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = _('Unprocessable entity.')
    default_code = 'unprocessable_entity'


class JsonApiParseError(ParseError):

    def __init__(self, id, detail, pointer, status=status.HTTP_400_BAD_REQUEST, code=None):
        self.status_code = status

        _detail = {
            "id": id,
            "detail": detail,
            "source": {
                "pointer": pointer,
            },
            "status": f"{self.status_code}"
        }

        # there is a bug described by https://github.com/django-json-api/django-rest-framework-json-api/issues/1140
        # thats why we pass in the details as array
        super().__init__([_detail], code)


class MissingPrimaryData(JsonApiParseError):

    def __init__(self, idx: int):
        super().__init__(
            "missing-primary-data",
            "primary data object musst be present",
            f"/atomic:operations/{idx}"
        )


class InvalidPrimaryDataType(JsonApiParseError):
    def __init__(self, idx, data_type: str):
        super().__init__(
            id="invalid-primary-data-type",
            detail=f"primary data object musst be an {data_type}",
            pointer=f"/atomic:operations/{idx}/data"
        )
