"""Encapsulates the invalid conditions that might occur during API execution."""
from homeassistant.const import (
    HTTP_OK,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_UNAUTHORIZED,
)


class HttpException(Exception):
    """Abstract exception, handled in the view."""

    def __init__(self, httpErrorCode, message, payload=None):
        """Create the exception object."""
        super().__init__(message)

        self.http_error_code = httpErrorCode
        self.payload = payload
        self.message = message


class ResourceNotFound(HttpException):
    """Resource wasn't found."""

    def __init__(self, message):
        """Exception constructor."""
        super().__init__(HTTP_NOT_FOUND, message)


class EntityNotFound(ResourceNotFound):
    """Resource wasn't found."""

    def __init__(self, entity_name):
        """Exception constructor."""
        super().__init__("Entity not found")


class Unauthorized(HttpException):
    """Request is not authorized."""

    def __init__(self, message):
        """Exception constructor."""
        super().__init__(HTTP_UNAUTHORIZED, message)


class EntityNotExposed(Unauthorized):
    """Requested entity wasn't exposed."""

    def __init__(self, entity):
        """Exception constructor."""
        super().__init__("Entity not exposed")


class HueException(HttpException):
    """An exception that produces a nicely formatted http message."""

    def __init__(
        self, error_type, address, description, http_error_code=HTTP_BAD_REQUEST
    ):
        """Exception constructor for well defined errors in hue api."""
        super().__init__(
            http_error_code,
            None,
            [
                {
                    "error": {
                        "type": error_type,
                        "address": address,
                        "description": description,
                    }
                }
            ],
        )


class UnauthorizedUser(HueException):
    """Provided user is not authorized to access the service."""

    def __init__(self):
        """Exception constructor."""
        super().__init__(1, "/", "unauthorized user", HTTP_OK)


class BadRequest(HttpException):
    """Generic exception for bad requests."""

    def __init__(self, message="Bad request", payload=None):
        """Exception constructor."""
        super().__init__(HTTP_BAD_REQUEST, message)


class InvalidJson(HueException):
    """JSON sent by client is invalid."""

    def __init__(self, path="/", description="body contains invalid json"):
        """Exception constructor."""
        super().__init__(2, path, description)


class InvalidValueForParameter(HueException):
    """Value sent by client isn't correct."""

    def __init__(self, path, parameter_name, parameter_value):
        """Create instance of the execption."""
        super().__init__(
            7,
            path,
            f"invalid value, {parameter_value}, for parameter, {parameter_name}",
        )
