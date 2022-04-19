"""Switch of the Xiaomi Plug/PowerStrip component."""
# pylint: disable=import-error
import asyncio
import logging
from datetime import timedelta
from functools import partial

from miio import DeviceException
import voluptuous as vol

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
    CONF_MAC
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.util import slugify
from homeassistant.components.xiaomi_miio.const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
)
from miio.powerstrip import PowerMode  # pylint: disable=import-error

from .const import (
    ATTR_POWER,
    ATTR_TEMPERATURE,
    ATTR_LOAD_POWER,
    ATTR_MODEL,
    ATTR_POWER_MODE,
    ATTR_WIFI_LED,
    ATTR_POWER_PRICE,
    ATTR_PRICE,
    ATTR_WORKING_TIME,
    ATTR_COUNT_DOWN_TIME,
    ATTR_KEEP_RELAY,
    CONF_MODEL,
    DATA_STATE,
    DATA_DEVICE,
    DATA_KEY,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_ZIMI_POWERSTRIP_V2,
    MODEL_CHUANGMI_PLUG_V3,
    MODEL_QMI_POWERSTRIP_2A1C1,
    MODELS_PLUG_WITH_USB_MIIO,
    MODELS_PLUG_MIIO,
    MODELS_POWERSTRIP_MIIO,
    MODELS_ACPARTNER_MIIO,
    MODELS_MIOT,
    MODELS_ALL_DEVICES
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

DEFAULT_NAME = DEFAULT_NAME + " Switch"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(MODELS_ALL_DEVICES),
    }
)

SUCCESS = ["ok"]

FEATURE_SET_POWER_MODE = 1
FEATURE_SET_WIFI_LED = 2
FEATURE_SET_POWER_PRICE = 4
FEATURE_SET_BUZZER = 8
FEATURE_COUNTDOWN = 16
FEATURE_SET_KEEP_RELAY = 32

FEATURE_FLAGS_GENERIC = 0

FEATURE_FLAGS_POWER_STRIP_V1 = (
    FEATURE_SET_POWER_MODE | FEATURE_SET_WIFI_LED | FEATURE_SET_POWER_PRICE
)

FEATURE_FLAGS_POWER_STRIP_V2 = FEATURE_SET_WIFI_LED | FEATURE_SET_POWER_PRICE

FEATURE_FLAGS_POWER_STRIP_V3 = (
    FEATURE_SET_POWER_MODE | FEATURE_SET_WIFI_LED | FEATURE_SET_BUZZER | FEATURE_COUNTDOWN | FEATURE_SET_KEEP_RELAY
)

FEATURE_FLAGS_PLUG_V3 = FEATURE_SET_WIFI_LED

FEATURE_FLAGS_GENERIC = 0


SERVICE_SET_WIFI_LED_ON = "switch_set_wifi_led_on"
SERVICE_SET_WIFI_LED_OFF = "switch_set_wifi_led_off"
SERVICE_SET_POWER_MODE = "switch_set_power_mode"
SERVICE_SET_POWER_PRICE = "switch_set_power_price"
SERVICE_START_COUNT_DOWN = "switch_start_count_down"
SERVICE_STOP_COUNT_DOWN = "switch_stop_count_down"
SERVICE_SET_COUNT_DOWN_TIME = "switch_set_count_down_time"
SERVICE_SET_KEEP_RELAY = "switch_set_keep_relay"
SERVICE_SET_NOT_KEEP_RELAY = "switch_set_not_keep_relay"

SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_POWER_MODE = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_MODE): vol.All(vol.In(["green", "normal"]))}
)

SERVICE_SCHEMA_POWER_PRICE = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_PRICE): vol.All(vol.Coerce(float), vol.Range(min=0))}
)

SERVICE_SCHEMA_COUNT_DOWN = SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_COUNT_DOWN_TIME): vol.All(vol.Coerce(int), vol.Range(min=0))}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_WIFI_LED_ON: {"method": "async_set_wifi_led_on"},
    SERVICE_SET_WIFI_LED_OFF: {"method": "async_set_wifi_led_off"},
    SERVICE_SET_POWER_MODE: {
        "method": "async_set_power_mode",
        "schema": SERVICE_SCHEMA_POWER_MODE,
    },
    SERVICE_SET_POWER_PRICE: {
        "method": "async_set_power_price",
        "schema": SERVICE_SCHEMA_POWER_PRICE,
    },
}

SERVICE_TO_METHOD_V2 = {
    SERVICE_START_COUNT_DOWN: {"method": "async_start_count_down"},
    SERVICE_STOP_COUNT_DOWN: {"method": "async_stop_count_down"},
    SERVICE_SET_COUNT_DOWN_TIME: {
        "method": "async_set_count_down_time",
        "schema": SERVICE_SCHEMA_COUNT_DOWN,
    },
    SERVICE_SET_KEEP_RELAY: {"method": "async_set_keep_relay"},
    SERVICE_SET_NOT_KEEP_RELAY: {"method": "async_set_not_keep_relay"},
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Xiaomi Plug/PowerStrip configuration from YAML."""
    _LOGGER.warning(
        "Loading Xiaomi Plug/PowerStrip via platform setup is deprecated; Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the switch from a config entry."""
    entities = []

    host = config_entry.options[CONF_HOST]
    token = config_entry.options[CONF_TOKEN]
    name = config_entry.title
    model = config_entry.options[CONF_MODEL]
    unique_id = config_entry.unique_id

    if config_entry.options[CONF_FLOW_TYPE] == CONF_DEVICE:
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        plug = hass.data[DOMAIN][host]
        if model in MODELS_PLUG_WITH_USB_MIIO:
            # The device has two switchable channels (mains and a USB port).
            # A switch device per channel will be created.
            for channel_usb in [True, False]:
                device = ChuangMiPlugSwitch(name, plug, model, unique_id, channel_usb)
                entities.append(device)
                hass.data[DATA_KEY][host] = device
        elif model in MODELS_POWERSTRIP_MIIO:
            device = XiaomiPowerStripSwitch(name, plug, model, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        elif model in MODELS_PLUG_MIIO:
            device = XiaomiPlugGenericSwitch(name, plug, model, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        elif model in MODELS_ACPARTNER_MIIO:
            device = XiaomiAirConditioningCompanionSwitch(name, plug, model, unique_id)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
            #hass.data[DATA_KEY][host][DATA_DEVICE] = device
        elif model in MODELS_MIOT:
            device = XiaomiPowerStripMiot(name, plug, model, unique_id, config_entry.options)
            entities.append(device)
            hass.data[DATA_KEY][host] = device
        else:
            _LOGGER.error(
                "Unsupported device found! Please create an issue at "
                "https://github.com/tsunglung/XiaomiPlug/issues "
                "and provide the following data: %s",
                model,
            )
            return

        async def async_service_handler(service):
            """Map services to methods on Xiaomi Plug/PowerStrip."""
            method = SERVICE_TO_METHOD.get(service.service)
            if method is None:
                method = SERVICE_TO_METHOD_V2.get(service.service)
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            entity_ids = service.data.get(ATTR_ENTITY_ID)
            if entity_ids:
                devices = [
                    device
                    for device in hass.data[DATA_KEY].values()
                    if device.entity_id in entity_ids
                ]
            else:
                devices = hass.data[DATA_KEY].values()
            update_tasks = []
            for device in devices:
                if not hasattr(device, method["method"]):
                    continue
                await getattr(device, method["method"])(**params)
                update_tasks.append(device.async_update_ha_state(True))

            if update_tasks:
                await asyncio.wait(update_tasks)

        for service, _ in SERVICE_TO_METHOD.items():
            schema = SERVICE_TO_METHOD[service].get("schema", SERVICE_SCHEMA)
            hass.services.async_register(
                DOMAIN, service, async_service_handler, schema=schema
            )
        if model in MODELS_MIOT:
            for service, _ in SERVICE_TO_METHOD_V2.items():
                schema = SERVICE_TO_METHOD_V2[service].get("schema", SERVICE_SCHEMA)
                hass.services.async_register(
                    DOMAIN, service, async_service_handler, schema=schema
                )


    async_add_entities(entities, update_before_add=False)


class XiaomiPlugGenericSwitch(SwitchEntity):
    """Representation of a Xiaomi Plug Generic."""

    def __init__(self, name, plug, model, unique_id):
        """Initialize the plug switch."""
        self._name = name
        self._plug = plug
        self._model = model
        self._unique_id = unique_id
        self._mac = None

        self._icon = "mdi:power-socket"
        self._available = False
        self._state = None
        self._status = None
        self._state_attrs = {ATTR_TEMPERATURE: None, ATTR_MODEL: self._model}
        self._device_features = FEATURE_FLAGS_GENERIC
        self._skip_update = False

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

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
    def status(self):
        """ Return the device status """
        return self._status

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a plug command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

            _LOGGER.debug("Response received from plug: %s", result)

            # The Chuangmi Plug V3 returns 0 on success on usb_on/usb_off.
            if func in ["usb_on", "usb_off"] and result == 0:
                return True

            return result == SUCCESS
        except DeviceException as exc:
            if self._available:
                _LOGGER.error(mask_error, exc)
                self._available = False

            return False

    async def async_turn_on(self, **kwargs):
        """Turn the plug on."""
        result = await self._try_command("Turning the plug on failed.", self._plug.on)

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs):
        """Turn the plug off."""
        result = await self._try_command("Turning the plug off failed.", self._plug.off)

        if result:
            self._state = False
            self._skip_update = True

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._plug.status)
            _LOGGER.debug("Got new state: %s", state)
            self._status = state

            self._available = True
            self._state = state.is_on
            self._state_attrs[ATTR_TEMPERATURE] = state.temperature

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_wifi_led_on(self):
        """Turn the wifi led on."""
        if self._device_features & FEATURE_SET_WIFI_LED == 0:
            return

        await self._try_command(
            "Turning the wifi led on failed.", self._plug.set_wifi_led, True
        )

    async def async_set_wifi_led_off(self):
        """Turn the wifi led on."""
        if self._device_features & FEATURE_SET_WIFI_LED == 0:
            return

        await self._try_command(
            "Turning the wifi led off failed.", self._plug.set_wifi_led, False
        )

    async def async_set_power_price(self, price: int):
        """Set the power price."""
        if self._device_features & FEATURE_SET_POWER_PRICE == 0:
            return

        await self._try_command(
            "Setting the power price of the power strip failed.",
            self._plug.set_power_price,
            price,
        )

    async def async_start_count_down(self):
        """Start count down."""
        if self._device_features & FEATURE_COUNTDOWN == 0:
            return

        await self._try_command(
            "Start count down failed.", self._plug.count_down, True
        )

    async def async_stop_count_down(self):
        """Stop count down."""
        if self._device_features & FEATURE_COUNTDOWN == 0:
            return

        await self._try_command(
            "Stop count down failed.", self._plug.count_down, False
        )

    async def async_set_count_down_time(self, price: int):
        """Set the count time."""
        if self._device_features & FEATURE_COUNTDOWN == 0:
            return

        await self._try_command(
            "Setting the count time of the power strip failed.",
            self._plug.set_count_down_time,
            price,
        )

    async def async_set_keep_relay(self):
        """Set keep relay."""
        if self._device_features & FEATURE_SET_KEEP_RELAY == 0:
            return

        await self._try_command(
            "Set keep relay failed.", self._plug.set_keep_relay, True
        )

    async def async_set_not_keep_relay(self):
        """Set Not keep relay."""
        if self._device_features & FEATURE_SET_KEEP_RELAY == 0:
            return

        await self._try_command(
            "Set not keep relay failed.", self._plug.set_keep_relay, False
        )


class XiaomiPowerStripSwitch(XiaomiPlugGenericSwitch):
    """Representation of a Xiaomi Power Strip."""

    def __init__(self, name, plug, model, unique_id):
        """Initialize the plug switch."""
        super().__init__(name, plug, model, unique_id)

        if self._model == MODEL_ZIMI_POWERSTRIP_V2:
            self._device_features = FEATURE_FLAGS_POWER_STRIP_V2
        else:
            self._device_features = FEATURE_FLAGS_POWER_STRIP_V1

        self._state_attrs[ATTR_LOAD_POWER] = None

        if self._device_features & FEATURE_SET_POWER_MODE == 1:
            self._state_attrs[ATTR_POWER_MODE] = None

        if self._device_features & FEATURE_SET_WIFI_LED == 1:
            self._state_attrs[ATTR_WIFI_LED] = None

        if self._device_features & FEATURE_SET_POWER_PRICE == 1:
            self._state_attrs[ATTR_POWER_PRICE] = None

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._plug.status)
            _LOGGER.debug("Got new state: %s", state)
            self._status = state

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {ATTR_TEMPERATURE: state.temperature, ATTR_LOAD_POWER: state.load_power}
            )

            if self._device_features & FEATURE_SET_POWER_MODE == 1 and state.mode:
                self._state_attrs[ATTR_POWER_MODE] = state.mode.value

            if self._device_features & FEATURE_SET_WIFI_LED == 1 and state.wifi_led:
                self._state_attrs[ATTR_WIFI_LED] = state.wifi_led

            if (
                self._device_features & FEATURE_SET_POWER_PRICE == 1
                and state.power_price
            ):
                self._state_attrs[ATTR_POWER_PRICE] = state.power_price

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_power_mode(self, mode: str):
        """Set the power mode."""
        if self._device_features & FEATURE_SET_POWER_MODE == 0:
            return

        await self._try_command(
            "Setting the power mode of the power strip failed.",
            self._plug.set_power_mode,
            PowerMode(mode),
        )


class ChuangMiPlugSwitch(XiaomiPlugGenericSwitch):
    """Representation of a Chuang Mi Plug V1 and V3."""

    def __init__(self, name, plug, model, unique_id, channel_usb):
        """Initialize the plug switch."""
        name = f"{name} USB" if channel_usb else name

        if unique_id is not None and channel_usb:
            unique_id = f"{unique_id}-usb"

        super().__init__(name, plug, model, unique_id)
        self._channel_usb = channel_usb

        if self._model == MODEL_CHUANGMI_PLUG_V3:
            self._device_features = FEATURE_FLAGS_PLUG_V3
            self._state_attrs[ATTR_WIFI_LED] = None
            if self._channel_usb is False:
                self._state_attrs[ATTR_LOAD_POWER] = None

    async def async_turn_on(self, **kwargs):
        """Turn a channel on."""
        if self._channel_usb:
            result = await self._try_command(
                "Turning the plug on failed.", self._plug.usb_on
            )
        else:
            result = await self._try_command(
                "Turning the plug on failed.", self._plug.on
            )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs):
        """Turn a channel off."""
        if self._channel_usb:
            result = await self._try_command(
                "Turning the plug on failed.", self._plug.usb_off
            )
        else:
            result = await self._try_command(
                "Turning the plug on failed.", self._plug.off
            )

        if result:
            self._state = False
            self._skip_update = True

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._plug.status)
            _LOGGER.debug("Got new state: %s", state)
            self._status = state

            self._available = True
            if self._channel_usb:
                self._state = state.usb_power
            else:
                self._state = state.is_on

            self._state_attrs[ATTR_TEMPERATURE] = state.temperature

            if state.wifi_led:
                self._state_attrs[ATTR_WIFI_LED] = state.wifi_led

            if self._channel_usb is False and state.load_power:
                self._state_attrs[ATTR_LOAD_POWER] = state.load_power

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)


class XiaomiAirConditioningCompanionSwitch(XiaomiPlugGenericSwitch):
    """Representation of a Xiaomi AirConditioning Companion."""

    def __init__(self, name, plug, model, unique_id):
        """Initialize the acpartner switch."""
        super().__init__(name, plug, model, unique_id)

        self._state_attrs.update({ATTR_TEMPERATURE: None, ATTR_LOAD_POWER: None})

    async def async_turn_on(self, **kwargs):
        """Turn the socket on."""
        result = await self._try_command(
            "Turning the socket on failed.", self._plug.socket_on
        )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs):
        """Turn the socket off."""
        result = await self._try_command(
            "Turning the socket off failed.", self._plug.socket_off
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._plug.status)
            _LOGGER.debug("Got new state: %s", state)
            self._status = state

            self._available = True
            self._state = state.power_socket == "on"
            self._state_attrs[ATTR_LOAD_POWER] = state.load_power

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)


class XiaomiPowerStripMiot(XiaomiPlugGenericSwitch):
    """Representation of a Xiaomi Power Strip Miot"""

    def __init__(self, name, plug, model, unique_id, config):
        """Initialize the plug switch."""
        super().__init__(name, plug, model, unique_id)
        self._mac = config.get(CONF_MAC, config.get(CONF_TOKEN))
        self._host = config[CONF_HOST]
        self._status = None

        if self._model == MODEL_QMI_POWERSTRIP_2A1C1:
            self._device_features = FEATURE_FLAGS_POWER_STRIP_V3
        else:
            self._device_features = 0

        self._state_attrs[ATTR_LOAD_POWER] = None

        if self._device_features & FEATURE_SET_POWER_MODE == 1:
            self._state_attrs[ATTR_POWER_MODE] = None

        if self._device_features & FEATURE_SET_WIFI_LED == 1:
            self._state_attrs[ATTR_WIFI_LED] = None

        if self._device_features & FEATURE_SET_POWER_PRICE == 1:
            self._state_attrs[ATTR_POWER_PRICE] = None

        self._state_attrs[ATTR_WORKING_TIME] = None
        self._state_attrs[ATTR_KEEP_RELAY] = None

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._plug.status)
            self._status = state
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {ATTR_TEMPERATURE: state.temperature, ATTR_LOAD_POWER: state.load_power}
            )

            if self._device_features & FEATURE_SET_POWER_MODE == 1 and state.mode:
                self._state_attrs[ATTR_POWER_MODE] = state.mode

            if self._device_features & FEATURE_SET_WIFI_LED == 1 and state.wifi_led:
                self._state_attrs[ATTR_WIFI_LED] = state.wifi_led

            self._state_attrs[ATTR_WORKING_TIME] = state.working_time
            self._state_attrs[ATTR_KEEP_RELAY] = state.keep_relay

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_power_mode(self, mode: str):
        """Set the power mode."""
        if self._device_features & FEATURE_SET_POWER_MODE == 0:
            return

        await self._try_command(
            "Setting the power mode of the power strip failed.",
            self._plug.set_power_mode,
            PowerMode(mode),
        )