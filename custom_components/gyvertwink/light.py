import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
    PLATFORM_SCHEMA,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import DOMAIN

from .gyver_twink import GyverTwink as GTwink

_LOGGER = logging.getLogger(__name__)

CONF_EFFECTS = "effects"


EFFECTS = [
    "Party grad",
    "Raibow grad",
    "Stripe grad",
    "Sunset grad",
    "Pepsi grad",
    "Warm grad",
    "Cold grad",
    "Hot grad",
    "Pink grad",
    "Cyber grad",
    "RedWhite grad",
    "Party noise",
    "Raibow noise",
    "Stripe noise",
    "Sunset noise",
    "Pepsi noise",
    "Warm noise",
    "Cold noise",
    "Hot noise",
    "Pink noise",
    "Cyber noise",
    "RedWhite noise",
]


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_EFFECTS): cv.ensure_list,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([GyverTwink(config)], True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    entity = GyverTwink(entry.options, entry.entry_id)
    async_add_entities([entity], True)

    hass.data[DOMAIN][entry.entry_id] = entity


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class GyverTwink(LightEntity):
    def __init__(self, config: dict, unique_id=None):
        self._attr_name = config.get(CONF_NAME, "Gyver Twink")
        self._attr_unique_id = unique_id

        #
        self._attr_effect_list = config.get(CONF_EFFECTS, EFFECTS)
        self._attr_should_poll = True
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_supported_features = LightEntityFeature.EFFECT

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="@AlexGyver",
            model="GyverTwink",
        )

        self.host = config[CONF_HOST]

    @property
    def address(self):
        return self.host

    @property
    def twink(self):
        return GTwink(self.address)

    def debug(self, message):
        _LOGGER.debug(f"{self.host} | {message}")

    def turn_on(
        self,
        brightness: int = None,
        effect: str = None,
    ):
        self.twink.on()

        try:
            if brightness:
                self.twink.set_brightness(brightness)
        except:
            self.debug(f"set_brightness/ {brightness}")

        try:
            if effect:
                eff_id = self._effects.index(effect)
                self.twink.select_effect(eff_id)
        except:
            self.debug(f"set_brightness/ {effect}")

    def turn_off(self, **kwargs):
        self.twink.off()

    def update(self):
        try:
            data = self.twink.get_settings()
            self.debug(f"UPDATE {data}")

            self._attr_is_on = data["power"]
            self._attr_brightness = int(data["brightness"])

            self._auto_change = data["auto_change"]
            self._random_change = data["random_change"]
            self._change_period = data["change_period"]
            self._is_timer_active = data["timer_active"]
            self._timer_value = data["timer_value"]

            self._effect = None

            self._attr_available = True

        except Exception as e:
            self.debug(f"Can't update: {e}")
            self._attr_available = False
