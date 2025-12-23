import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import GyverTwinkCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Настройка button entity для переключения эффектов."""
    
    # Получаем coordinator из hass.data
    coordinator: GyverTwinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Создаем button entity
    entity = GyverTwinkNextEffect(coordinator, entry.entry_id)
    
    async_add_entities([entity], True)


class GyverTwinkNextEffect(CoordinatorEntity, ButtonEntity):
    """Button entity для переключения на следующий эффект.
    
    Эквивалент кнопки в родном приложении - переключает эффекты по порядку.
    """
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация NextEffect button."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Next Effect"
        self._attr_unique_id = f"{unique_id}_next_effect"
        self._attr_icon = "mdi:skip-next"
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | NextEffect | {message}")

    async def async_press(self) -> None:
        """Обработка нажатия кнопки - переключение на следующий эффект."""
        try:
            # Вызываем метод next_effect через coordinator
            await self.coordinator.async_next_effect()
            
            self.debug("Switched to next effect")
            
            # Обновляем состояние для синхронизации
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error switching effect: {e}")
            raise

