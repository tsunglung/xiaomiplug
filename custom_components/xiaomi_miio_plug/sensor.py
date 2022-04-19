"""Support for Xiaomi Plug/PowerStrip service."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_HOST,
    CONF_TOKEN
)
from miio import DeviceException

from .switch_miot import SystemStatus
from .const import (
    CONF_MODEL,
    DATA_KEY,
    DATA_STATE,
    DOMAIN,
    PLUG_SENSORS,
    MODEL_CHUANGMI_PLUG_V3,
    MODELS_POWERSTRIP_MIIO,
    MODELS_MIOT,
    XiaomiPlugSensorDescription
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the plug/powerstrip sensor."""

    host = entry.options[CONF_HOST]
    model = entry.options[CONF_MODEL]
    name = entry.title
    unique_id = entry.unique_id

    plug = hass.data[DOMAIN][host]

    try:
        entities = []

        for description in PLUG_SENSORS:
            if ((description.key == "load_power") and
                (model in MODELS_POWERSTRIP_MIIO or model == MODEL_CHUANGMI_PLUG_V3)):
                    entities.extend(
                        [XiaomiPlugSensor(entry.options, description, name, unique_id, plug)]
                    )
            elif model in MODELS_MIOT:
                entities.extend(
                    [XiaomiPlugSensor(entry.options, description, name, unique_id, plug)]
                )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

class XiaomiPlugSensor(SensorEntity):
    """Implementation of a xiaomi plug sensor."""
    entity_description: XiaomiPlugSensorDescription

    def __init__(self, entry_data, description, name, unique_id, plug):
        self.entity_description = description
        self._entry_data = entry_data
        self._name = name
        self._model = entry_data[CONF_MODEL]
        self._unique_id = unique_id
        self._attr = description.key
        self._mac = entry_data[CONF_TOKEN]
        self._host = entry_data[CONF_HOST]
        self._plug = plug
        self._available = True
        self._skip_update = False
        self._state = None
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {}".format(self._name, self.entity_description.name)

    @property
    def unique_id(self):
        """Return the unique of the sensor."""
        return "{}_{}".format(self._name, self.entity_description.key)

    def friendly_name(self):
        """Return the friendly name of the sensor."""
        return "{}".format(self.entity_description.name)

    @property
    def device_info(self):
        """Return the device info."""
        info = self._plug.info()
        device_info = {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": (self._model or "Xiaomi").split(".", 1)[0].capitalize(),
            "name": self._name,
            "model": self._model,
            "sw_version": info.firmware_version,
            "hw_version": info.hardware_version
        }

        if self._mac is not None:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, self._mac)}

        return device_info

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            if getattr(self.hass.data[DATA_KEY][self._host], "status", None):
                state = self.hass.data[DATA_KEY][self._host].status
            else:
                state = await self.hass.async_add_executor_job(self._plug.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = getattr(state, self._attr, None)
            if self.entity_description.device_class == SensorDeviceClass.VOLTAGE:
                self._state = self._state / 1000
            if self.entity_description.device_class == SensorDeviceClass.DATE:
                self._state = timedelta(seconds=self._state)
            if self.entity_description.key == "system_status":
                self._state = SystemStatus(self._state).name

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

