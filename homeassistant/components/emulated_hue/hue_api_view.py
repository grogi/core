"""Abstract view for all hue api calls. This provides authorization handling, error handling and convenience methods."""
import asyncio
import logging

from homeassistant.components.http.view import HomeAssistantView, encode_result
from homeassistant.components.http.const import KEY_HASS, KEY_REAL_IP
from homeassistant.components.emulated_hue.exceptions import (
    HttpException,
    EntityNotExposed,
    EntityNotFound,
    UnauthorizedUser,
    Unauthorized,
)
from homeassistant.core import is_callback
from homeassistant.util.network import is_local

_LOGGER = logging.getLogger(__name__)

HUE_API_USERNAME = "nouser"


class HueApiView(HomeAssistantView):
    """A special view that is used by hue emulation."""

    def __init__(self, config=None):
        """Initialize the instance of the view."""
        self.config = config

    # Elegant way of exposing it to inheriting objects
    # pylint: disable=no-self-use
    def get_hass_app(self, request):
        """Return the hass object from the request."""
        return request.app[KEY_HASS]

    def get_hass_entity(self, request, entity_number):
        """Retrieve the hass entity based on the given entity_number."""
        hass = self.get_hass_app(request)
        hass_entity_id = self.config.number_to_entity_id(entity_number)

        if hass_entity_id is None:
            _LOGGER.error(
                "Unknown entity number: %s not found in emulated_hue_ids.json",
                entity_number,
            )
            raise EntityNotFound(entity_number)

        entity = hass.states.get(hass_entity_id)

        if entity is None:
            _LOGGER.error("Entity not found: %s", hass_entity_id)
            raise EntityNotFound(entity_number)

        if not self.config.is_entity_exposed(entity):
            _LOGGER.error("Entity not exposed: %s", entity_number)
            raise EntityNotExposed(entity_number)

        return entity, hass_entity_id

    def get_request_handler_factory(self):
        """Return the request_factory to be used during registering the view."""
        return hue_api_request_factory


def hue_api_request_factory(view, handler):
    """Wrap the handler classes."""
    assert asyncio.iscoroutinefunction(handler) or is_callback(
        handler
    ), "Handler should be a coroutine or a callback."

    async def handle(request):
        """Handle incoming request."""
        try:
            if not request.app[KEY_HASS].is_running:
                raise HttpException(503, None)

            # Check if requests originates at a local IP
            if not is_local(request[KEY_REAL_IP]):
                raise Unauthorized("Only local IPs allowed")

            # If view.requires_auth, check if the username is authenticated
            if view.requires_auth:
                user = view.config.get_whitelisted_user(request.match_info["username"])

                if user is None:
                    raise UnauthorizedUser()

                view.config.touch_whitelisted_user(request.match_info["username"])

            result = handler(request, **request.match_info)

            if asyncio.iscoroutine(result):
                result = await result
        except HttpException as ex:
            if ex.payload is not None:
                result = HomeAssistantView.json(ex.payload, ex.http_error_code)
            else:
                result = HomeAssistantView.json_message(ex.message, ex.http_error_code)

        return encode_result(result)

    return handle
