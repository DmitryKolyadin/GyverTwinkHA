import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import GyverTwinkCoordinator

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
    """Настройка платформы через YAML (legacy)."""
    # Для YAML конфигурации создаем упрощенный entity без coordinator
    unique_id = config.get(CONF_HOST, "gyvertwink").replace(".", "_")
    add_entities([GyverTwinkLight(config, unique_id, None)], True)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Настройка из config entry."""
    # Получаем coordinator из hass.data
    coordinator: GyverTwinkCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Создаем light entity с coordinator
    entity = GyverTwinkLight(entry.options, entry.entry_id, coordinator)
    async_add_entities([entity], True)


class GyverTwinkLight(CoordinatorEntity, LightEntity):
    """Light entity для управления GyverTwink гирляндой."""

    def __init__(
        self,
        config: dict,
        unique_id: str,
        coordinator: GyverTwinkCoordinator | None,
    ):
        """Инициализация light entity."""
        # Инициализируем CoordinatorEntity если coordinator доступен
        if coordinator:
            super().__init__(coordinator)

        self._attr_name = config.get(CONF_NAME, "Gyver Twink")
        self._attr_unique_id = unique_id
        self.host = config[CONF_HOST]
        self._coordinator = coordinator

        # Настройки light
        self._attr_effect_list = config.get(CONF_EFFECTS, EFFECTS)
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_features = LightEntityFeature.EFFECT

        # Информация об устройстве
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="@AlexGyver",
            model="GyverTwink",
            name=self._attr_name,
        )

        # Текущий эффект
        self._attr_effect = None
        self._current_effect_index = 0

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.host} | Light | {message}")

    async def async_turn_on(self, **kwargs):
        """Включение гирлянды."""
        brightness = kwargs.get("brightness")
        effect = kwargs.get("effect")

        try:
            # Включаем гирлянду через coordinator
            if self._coordinator:
                await self._coordinator.async_set_power(True)
            else:
                # Fallback для YAML конфигурации без coordinator
                await self.hass.async_add_executor_job(
                    self._coordinator.twink.set_power, True
                )

            # Устанавливаем яркость если указана
            if brightness is not None:
                if self._coordinator:
                    await self._coordinator.async_set_brightness(brightness)
                self._attr_brightness = brightness
                self.debug(f"Brightness set to: {brightness}")

            # Устанавливаем эффект если указан
            if effect is not None:
                try:
                    eff_id = self._attr_effect_list.index(effect)
                    if self._coordinator:
                        await self._coordinator.async_select_effect(eff_id)

                    self._attr_effect = effect
                    self._current_effect_index = eff_id
                    self.debug(f"Effect set to: {effect} (ID: {eff_id})")

                except ValueError:
                    self.debug(f"Effect not found: {effect}")
                except Exception as e:
                    self.debug(f"Error setting effect: {e}")

            self._attr_is_on = True

        except Exception as e:
            self.debug(f"Error in turn_on: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Выключение гирлянды."""
        try:
            if self._coordinator:
                await self._coordinator.async_set_power(False)
            else:
                # Fallback для YAML конфигурации
                await self.hass.async_add_executor_job(
                    self._coordinator.twink.set_power, False
                )

            self._attr_is_on = False
            self.debug("Turned off")

        except Exception as e:
            self.debug(f"Error in turn_off: {e}")
            raise

    @property
    def available(self) -> bool:
        """Доступность entity.

        CoordinatorEntity автоматически управляет доступностью на основе
        успешности обновлений coordinator.
        """
        if self._coordinator:
            return self._coordinator.last_update_success
        return True

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator.

        Этот метод вызывается автоматически когда coordinator получает новые данные.
        Все entities получают данные из одного запроса - нет множественных таймаутов.
        """
        if not self._coordinator or not self.coordinator.data:
            return

        data = self.coordinator.data
        self.debug(f"Coordinator update: {data}")

        # Обновляем состояние на основе данных от устройства
        self._attr_is_on = data.get("power", False)
        self._attr_brightness = int(data.get("brightness", 0))

        # Записываем обновленное состояние
        self.async_write_ha_state()
