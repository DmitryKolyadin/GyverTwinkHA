"""DataUpdateCoordinator для GyverTwink."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .gyver_twink import GyverTwink as GTwink

_LOGGER = logging.getLogger(__name__)


class GyverTwinkCoordinator(DataUpdateCoordinator):
    """Координатор обновлений для GyverTwink.
    
    Делает один запрос к устройству и распределяет данные между всеми entities.
    Это предотвращает множественные одновременные запросы и таймауты.
    """

    def __init__(self, hass: HomeAssistant, host: str, entry_id: str) -> None:
        """Инициализация координатора."""
        self.host = host
        self.entry_id = entry_id
        self.twink = GTwink(host)
        
        # Интервал опроса - можно настроить от 5 до 60 секунд
        # Рекомендуется: 10-15 секунд для быстрого отклика
        # По умолчанию: 15 секунд (баланс между скоростью и нагрузкой)
        super().__init__(
            hass,
            _LOGGER,
            name=f"GyverTwink {host}",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Получение данных от устройства.
        
        Этот метод вызывается автоматически каждые 15 секунд.
        Все entities получат эти данные без дополнительных запросов.
        """
        try:
            # Выполняем запрос в executor thread (блокирующая операция)
            data = await self.hass.async_add_executor_job(self.twink.get_settings)
            
            if data is None:
                raise UpdateFailed("Device returned no data")
            
            _LOGGER.debug(f"{self.host} | Coordinator update: {data}")
            return data
            
        except Exception as err:
            _LOGGER.error(f"{self.host} | Error fetching data: {err}")
            raise UpdateFailed(f"Error communicating with device: {err}")

    async def async_set_power(self, state: bool) -> None:
        """Установка питания с немедленным обновлением данных."""
        await self.hass.async_add_executor_job(self.twink.set_power, state)
        await self.async_request_refresh()

    async def async_set_brightness(self, value: int) -> None:
        """Установка яркости с немедленным обновлением данных."""
        await self.hass.async_add_executor_job(self.twink.set_brightness, value)
        await self.async_request_refresh()

    async def async_select_effect(self, effect_id: int) -> dict | None:
        """Выбор эффекта и получение его параметров."""
        result = await self.hass.async_add_executor_job(
            self.twink.select_effect, effect_id
        )
        await self.async_request_refresh()
        return result

    async def async_set_auto_change(self, state: bool) -> None:
        """Установка автосмены эффектов."""
        await self.hass.async_add_executor_job(self.twink.set_auto_change, state)
        await self.async_request_refresh()

    async def async_set_random_change(self, state: bool) -> None:
        """Установка случайной смены эффектов."""
        await self.hass.async_add_executor_job(self.twink.set_random_change, state)
        await self.async_request_refresh()

    async def async_set_change_period(self, value: int) -> None:
        """Установка периода смены эффектов."""
        await self.hass.async_add_executor_job(self.twink.set_change_period, value)
        await self.async_request_refresh()

    async def async_set_timer(self, state: bool) -> None:
        """Установка таймера выключения."""
        await self.hass.async_add_executor_job(self.twink.set_timer, state)
        await self.async_request_refresh()

    async def async_set_timer_value(self, value: int) -> None:
        """Установка времени таймера."""
        await self.hass.async_add_executor_job(self.twink.set_timer_value, value)
        await self.async_request_refresh()

    async def async_set_leds(self, count: int) -> None:
        """Установка количества светодиодов."""
        await self.hass.async_add_executor_job(self.twink.set_leds, count)
        await self.async_request_refresh()

    async def async_set_speed(self, value: int) -> None:
        """Установка скорости эффекта."""
        await self.hass.async_add_executor_job(self.twink.set_speed, value)
        # Не обновляем данные, т.к. speed не возвращается в get_settings

    async def async_set_scale(self, value: int) -> None:
        """Установка масштаба эффекта."""
        await self.hass.async_add_executor_job(self.twink.set_scale, value)
        # Не обновляем данные, т.к. scale не возвращается в get_settings

    async def async_next_effect(self) -> None:
        """Переключение на следующий эффект."""
        await self.hass.async_add_executor_job(self.twink.next_effect)
        # Не обновляем данные, т.к. текущий эффект не возвращается в get_settings

