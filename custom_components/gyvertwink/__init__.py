from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import GyverTwinkCoordinator

DOMAIN = "gyvertwink"


async def async_setup(hass, hass_config):
    """Настройка интеграции (используется только для GUI setup)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Настройка из config entry."""
    # Миграция данных (после первой настройки) в options
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={}, options=entry.data)

    # Создаем координатор для централизованного опроса устройства
    # Это предотвращает множественные запросы и таймауты
    coordinator = GyverTwinkCoordinator(
        hass,
        entry.options[CONF_HOST],
        entry.entry_id,
    )

    # Первичное получение данных
    await coordinator.async_config_entry_first_refresh()

    # Сохраняем coordinator для доступа из entities
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Добавляем обработчик обновления опций
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Пробрасываем настройку на платформы light, number, switch и button
    await hass.config_entries.async_forward_entry_setups(
        entry, ["light", "number", "switch", "button"]
    )

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Обработка обновления опций."""
    # Перезагружаем entry для применения новых настроек
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Выгрузка config entry."""
    # Выгружаем все платформы
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["light", "number", "switch", "button"]
    )

    # Удаляем coordinator из памяти
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
