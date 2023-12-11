import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (
    PLATFORM_SCHEMA,
    LightEntity,
    SUPPORT_BRIGHTNESS,
    SUPPORT_EFFECT,
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

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
    _available = False
    _brightness = None
    _host = None
    _is_on = None

    _effect = None
    _effects = None

    _twink = None

    def __init__(self, config: dict, unique_id=None):
        self._name = config.get(CONF_NAME, "Gyver Twink")
        self._unique_id = unique_id

        self.update_config(config)

    @property
    def should_poll(self):
        return True

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def brightness(self):
        return self._brightness

    @property
    def effect_list(self):
        return self._effects

    @property
    def effect(self):
        return self._effect

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_EFFECT

    @property
    def is_on(self):
        return self._is_on

    @property
    def available(self):
        return self._available

    @property
    def device_info(self):
        """
        https://developers.home-assistant.io/docs/device_registry_index/
        """
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": "@AlexGyver",
            "model": "GyverTwink",
        }

    @property
    def address(self):
        return self._host

    @property
    def twink(self):
        return GTwink(self.address)

    def debug(self, message):
        _LOGGER.debug(f"{self._host} | {message}")

    def update_config(self, config: dict):
        self._effects = config.get(CONF_EFFECTS, EFFECTS)
        self._host = config[CONF_HOST]

        if self.hass:
            self._async_write_ha_state()

    def turn_on(self, **kwargs):
        self.twink.on()

        try:
            self.twink.set_brightness(kwargs[ATTR_BRIGHTNESS])
        except:
            self.debug(f"set_brightness/ {kwargs}")

        try:
            eff_name = kwargs[ATTR_EFFECT]
            eff_id = self._effects.index(eff_name)

            self.twink.select_effect(eff_id)
        except:
            self.debug(f"set_brightness/ {kwargs}")

    def turn_off(self, **kwargs):
        self.twink.off()

    def update(self):
        try:
            data = self.twink.get_settings()
            self.debug(f"UPDATE {data}")

            self._is_on = data["power"]
            self._brightness = int(data["brightness"])

            self._auto_change = data["auto_change"]
            self._random_change = data["random_change"]
            self._change_period = data["change_period"]
            self._is_timer_active = data["timer_active"]
            self._timer_value = data["timer_value"]

            self._effect = None

            self._available = True

        except Exception as e:
            self.debug(f"Can't update: {e}")
            self._available = False
