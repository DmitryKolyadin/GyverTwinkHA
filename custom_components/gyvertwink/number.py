import logging

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Настройка number entities для управления параметрами эффектов."""
    
    # Получаем coordinator из hass.data
    coordinator: GyverTwinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Создаем все number entities с coordinator
    entities = [
        GyverTwinkSpeed(coordinator, entry.entry_id),
        GyverTwinkScale(coordinator, entry.entry_id),
        GyverTwinkChangePeriod(coordinator, entry.entry_id),
        GyverTwinkLEDAmount(coordinator, entry.entry_id),
        GyverTwinkTimerValue(coordinator, entry.entry_id),
    ]
    
    async_add_entities(entities, True)


class GyverTwinkSpeed(CoordinatorEntity, NumberEntity):
    """Number entity для управления скоростью эффекта (1-127)."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация Speed entity."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Speed"
        self._attr_unique_id = f"{unique_id}_speed"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 127
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:speedometer"
        
        # Начальное значение
        self._attr_native_value = 64
        self._direction = False  # False = прямое, True = обратное
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | Speed | {message}")

    def _calculate_speed_value(self, speed: int, direction: bool) -> int:
        """Вычисляет итоговое значение скорости с учетом направления.
        
        Протокол GyverTwink: 128 - центр, <128 - вперед, >128 - назад.
        """
        if direction:
            return 128 + speed
        else:
            return 128 - speed

    async def async_set_native_value(self, value: float) -> None:
        """Устанавливает скорость эффекта."""
        try:
            speed = int(value)
            final_speed = self._calculate_speed_value(speed, self._direction)
            
            await self.coordinator.async_set_speed(final_speed)
            
            self._attr_native_value = speed
            
            direction_str = "REVERSE" if self._direction else "FORWARD"
            self.debug(f"Speed: {speed}, Direction: {direction_str}, Final: {final_speed}")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error setting speed: {e}")
            raise

    def set_direction(self, direction: bool) -> None:
        """Устанавливает направление (вызывается из Direction switch)."""
        self._direction = direction


class GyverTwinkScale(CoordinatorEntity, NumberEntity):
    """Number entity для управления масштабом (пятном) эффекта."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация Scale entity."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Scale"
        self._attr_unique_id = f"{unique_id}_scale"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 255
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:resize"
        
        self._attr_native_value = 128
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | Scale | {message}")

    async def async_set_native_value(self, value: float) -> None:
        """Устанавливает масштаб эффекта."""
        try:
            scale = int(value)
            await self.coordinator.async_set_scale(scale)
            
            self._attr_native_value = scale
            
            self.debug(f"Scale set to: {scale}")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error setting scale: {e}")
            raise


class GyverTwinkChangePeriod(CoordinatorEntity, NumberEntity):
    """Number entity для управления периодом смены эффектов (1-10 минут)."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация ChangePeriod entity."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Change Period"
        self._attr_unique_id = f"{unique_id}_change_period"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 10
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:timer-outline"
        self._attr_native_unit_of_measurement = "min"
        
        self._attr_native_value = 5
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | ChangePeriod | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное значение от устройства
            period = self.coordinator.data.get("change_period")
            if period is not None:
                self._attr_native_value = period
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Устанавливает период смены эффектов."""
        try:
            period = int(value)
            await self.coordinator.async_set_change_period(period)
            
            self._attr_native_value = period
            
            self.debug(f"Change period set to: {period} min")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error setting change period: {e}")
            raise


class GyverTwinkLEDAmount(CoordinatorEntity, NumberEntity):
    """Number entity для настройки количества светодиодов."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация LEDAmount entity."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink LED Amount"
        self._attr_unique_id = f"{unique_id}_led_amount"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 1000
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:led-strip-variant"
        
        self._attr_native_value = 100
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | LEDAmount | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное количество LED от устройства
            leds = self.coordinator.data.get("leds")
            if leds is not None:
                self._attr_native_value = leds
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Устанавливает количество светодиодов."""
        try:
            led_count = int(value)
            await self.coordinator.async_set_leds(led_count)
            
            self._attr_native_value = led_count
            
            self.debug(f"LED amount set to: {led_count}")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error setting LED amount: {e}")
            raise


class GyverTwinkTimerValue(CoordinatorEntity, NumberEntity):
    """Number entity для настройки времени таймера выключения (1-240 минут)."""
    
    def __init__(self, coordinator: GyverTwinkCoordinator, unique_id: str):
        """Инициализация TimerValue entity."""
        super().__init__(coordinator)
        
        self._attr_name = "Gyver Twink Turn Off In"
        self._attr_unique_id = f"{unique_id}_timer_value"
        self._attr_native_min_value = 1
        self._attr_native_max_value = 240
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_icon = "mdi:timer-off-outline"
        self._attr_native_unit_of_measurement = "min"
        
        self._attr_native_value = 60
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
        )

    def debug(self, message):
        """Логирование отладочной информации."""
        _LOGGER.debug(f"{self.coordinator.host} | TimerValue | {message}")

    def _handle_coordinator_update(self) -> None:
        """Обработка обновления данных от coordinator."""
        if self.coordinator.data:
            # Получаем актуальное значение таймера от устройства
            timer_value = self.coordinator.data.get("timer_value")
            if timer_value is not None:
                self._attr_native_value = timer_value
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Устанавливает время таймера выключения."""
        try:
            timer_minutes = int(value)
            await self.coordinator.async_set_timer_value(timer_minutes)
            
            self._attr_native_value = timer_minutes
            
            self.debug(f"Timer value set to: {timer_minutes} min")
            self.async_write_ha_state()
            
        except Exception as e:
            self.debug(f"Error setting timer value: {e}")
            raise
