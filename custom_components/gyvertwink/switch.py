import logging

from homeassistant.components.switch import SwitchEntity
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
    """Настройка switch entities для управления направлением и режимами."""
    
    # Получаем coordinator из hass.data
    coordinator: GyverTwinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Создаем все switch entities с coordinator
    entities = [
        GyverTwinkDirection(coordinator, entry.entry_id, hass),
        GyverTwinkAutoChange(coordinator, entry.entry_id),
        GyverTwinkRandomChange(coordinator, entry.entry_id),
        GyverTwinkOffTimer(coordinator, entry.entry_id),
    ]
    
    async_add_entities(entities, True)


class GyverTwinkDirection(CoordinatorEntity, SwitchEntity):
    """Switch entity для управления направлением движения эффекта.
    
    OFF = Прямое направление (Forward)
    ON = Обратное направление (Reverse)
    """
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str, hass):
        """Инициализация Direction switch."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Direction"
        self._attr_unique_id = f"{unique_id}_direction"
        self._attr_icon = "mdi:swap-horizontal"
        
        self.hass = hass
        self.entry_id = unique_id
        self._attr_is_on = False  # False = Forward, True = Reverse
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | Direction | {message}")

    def _get_speed_entity(self):
        """Получает Speed entity для синхронизации направления."""
        from homeassistant.helpers import entity_registry
        er = entity_registry.async_get(self.hass)
        
        speed_unique_id = f"{self.entry_id}_speed"
        entity_id = er.async_get_entity_id("number", DOMAIN, speed_unique_id)
        
        if entity_id:
            # Получаем entity из entity component
            entity_comp = self.hass.data.get("entity_components", {}).get("number")
            if entity_comp:
                return entity_comp.get_entity(entity_id)
        return None

    def _calculate_speed_value(self, speed: int, direction: bool) -> int:
        """Вычисляет итоговое значение скорости с учетом направления."""
        if direction:
            return 128 + speed
        else:
            return 128 - speed

    async def async_turn_on(self, **kwargs):
        """Включить обратное направление (Reverse)."""
        try:
            self._attr_is_on = True
            
            # Получаем текущую скорость из Speed entity
            speed_entity = self._get_speed_entity()
            current_speed = 64  # default
            if speed_entity and hasattr(speed_entity, '_attr_native_value'):
                current_speed = int(speed_entity._attr_native_value)
                # Уведомляем Speed entity о смене направления
                speed_entity.set_direction(True)
            
            # Вычисляем финальное значение и отправляем на устройство
            final_speed = self._calculate_speed_value(current_speed, True)
            await self.coordinator.async_set_speed(final_speed)
            
            self.debug(f"Direction REVERSE (speed: {current_speed}, final: {final_speed})")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error turning on: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Включить прямое направление (Forward)."""
        try:
            self._attr_is_on = False
            
            # Получаем текущую скорость из Speed entity
            speed_entity = self._get_speed_entity()
            current_speed = 64  # default
            if speed_entity and hasattr(speed_entity, '_attr_native_value'):
                current_speed = int(speed_entity._attr_native_value)
                # Уведомляем Speed entity о смене направления
                speed_entity.set_direction(False)
            
            # Вычисляем финальное значение и отправляем на устройство
            final_speed = self._calculate_speed_value(current_speed, False)
            await self.coordinator.async_set_speed(final_speed)
            
            self.debug(f"Direction FORWARD (speed: {current_speed}, final: {final_speed})")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error turning off: {e}")
            raise


class GyverTwinkAutoChange(CoordinatorEntity, SwitchEntity):
    """Switch entity для автоматической смены эффектов."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация AutoChange switch."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Auto Change"
        self._attr_unique_id = f"{unique_id}_auto_change"
        self._attr_icon = "mdi:autorenew"
        
        self._attr_is_on = False
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | AutoChange | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное состояние от устройства
            auto_change = self.coordinator.data.get("auto_change")
            if auto_change is not None:
                self._attr_is_on = auto_change
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Включить автосмену эффектов."""
        try:
            await self.coordinator.async_set_auto_change(True)
            self._attr_is_on = True
            self.debug("Auto change enabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Выключить автосмену эффектов."""
        try:
            await self.coordinator.async_set_auto_change(False)
            self._attr_is_on = False
            self.debug("Auto change disabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise


class GyverTwinkRandomChange(CoordinatorEntity, SwitchEntity):
    """Switch entity для случайной смены эффектов."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация RandomChange switch."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Random Change"
        self._attr_unique_id = f"{unique_id}_random_change"
        self._attr_icon = "mdi:shuffle-variant"
        
        self._attr_is_on = False
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | RandomChange | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное состояние от устройства
            random_change = self.coordinator.data.get("random_change")
            if random_change is not None:
                self._attr_is_on = random_change
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Включить случайную смену эффектов."""
        try:
            await self.coordinator.async_set_random_change(True)
            self._attr_is_on = True
            self.debug("Random change enabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Выключить случайную смену эффектов."""
        try:
            await self.coordinator.async_set_random_change(False)
            self._attr_is_on = False
            self.debug("Random change disabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise


class GyverTwinkOffTimer(CoordinatorEntity, SwitchEntity):
    """Switch entity для включения таймера выключения."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация OffTimer switch."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Off Timer"
        self._attr_unique_id = f"{unique_id}_off_timer"
        self._attr_icon = "mdi:timer-off"
        
        self._attr_is_on = False
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | OffTimer | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное состояние от устройства
            timer_active = self.coordinator.data.get("timer_active")
            if timer_active is not None:
                self._attr_is_on = timer_active
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Включить таймер выключения."""
        try:
            await self.coordinator.async_set_timer(True)
            self._attr_is_on = True
            self.debug("Off timer enabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise

    async def async_turn_off(self, **kwargs):
        """Выключить таймер выключения."""
        try:
            await self.coordinator.async_set_timer(False)
            self._attr_is_on = False
            self.debug("Off timer disabled")
            self.async_write_ha_state()
        except Exception as e:
            self.debug(f"Error: {e}")
            raise
