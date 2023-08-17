"""Constants of the Xiaomi Plug/PowerStrip component."""
from datetime import timedelta
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass
)

from homeassistant.const import (
    ELECTRIC_POTENTIAL_VOLT,
    ELECTRIC_CURRENT_MILLIAMPERE,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    TIME_SECONDS
)

DEFAULT_NAME = "Xiaomi Switch"
DOMAIN = "xiaomi_miio_plug"
DOMAINS = ["sensor", "switch"]
DATA_KEY = "xiaomi_switch_data"
DATA_STATE = "state"
DATA_DEVICE = "device"

CONF_MODEL = "model"
CONF_MAC = "mac"

MODEL_CHUANGMI_PLUG_V1 = "chuangmi.plug.v1"
MODEL_QMI_POWERSTRIP_V1 = "qmi.powerstrip.v1"
MODEL_QMI_POWERSTRIP_2A1C1 = "qmi.plug.2a1c1"
MODEL_ZIMI_POWERSTRIP_V2 = "zimi.powerstrip.v2"
MODEL_CHUANGMI_PLUG_M1 = "chuangmi.plug.m1"
MODEL_CHUANGMI_PLUG_M3 = "chuangmi.plug.m3"
MODEL_CHUANGMI_PLUG_V2 = "chuangmi.plug.v2"
MODEL_CHUANGMI_PLUG_V3 = "chuangmi.plug.v3"
MODEL_CHUANGMI_PLUG_HMI205 = "chuangmi.plug.hmi205"
MODEL_CHUANGMI_PLUG_HMI206 = "chuangmi.plug.hmi206"
MODEL_CHUANGMI_PLUG_HMI208 = "chuangmi.plug.hmi208"
MODEL_LUMI_ACPARTNER_V3 = "lumi.acpartner.v3"
MODEL_QMI_PLUG_TW02 = "qmi.plug.tw02"

OPT_MODEL = {
    MODEL_CHUANGMI_PLUG_V1: "Mi Smart Plug",
    MODEL_QMI_POWERSTRIP_V1: "Mi PowerStrip (China)",
    MODEL_QMI_POWERSTRIP_2A1C1: "Mi PowerStrip (Global)",
    MODEL_ZIMI_POWERSTRIP_V2: "Mi PowerStrip V2",
    MODEL_CHUANGMI_PLUG_M1: "Mi Plug M1",
    MODEL_CHUANGMI_PLUG_M3: "Mi Plug M3",
    MODEL_CHUANGMI_PLUG_V2: "Mi Plug V2",
    MODEL_CHUANGMI_PLUG_V3: "Mi Plug V3",
    MODEL_CHUANGMI_PLUG_HMI205: "Mi Plug HMI205",
    MODEL_CHUANGMI_PLUG_HMI206: "Mi Plug HMI206",
    MODEL_CHUANGMI_PLUG_HMI208: "Mi Plug HMI208",
    MODEL_LUMI_ACPARTNER_V3: "Mi AC Partner (upgrade)",
    MODEL_QMI_PLUG_TW02: "Mi Plug TW02"
}

MODELS_PLUG_MIIO = [
    MODEL_CHUANGMI_PLUG_M1,
    MODEL_CHUANGMI_PLUG_M3,
    MODEL_CHUANGMI_PLUG_V2,
    MODEL_CHUANGMI_PLUG_HMI205,
    MODEL_CHUANGMI_PLUG_HMI206
]

MODELS_PLUG_WITH_USB_MIIO = [
    MODEL_CHUANGMI_PLUG_V1,
    MODEL_CHUANGMI_PLUG_V3,
    MODEL_CHUANGMI_PLUG_HMI208
]

MODELS_POWERSTRIP_MIIO = [
    MODEL_QMI_POWERSTRIP_V1,
    MODEL_ZIMI_POWERSTRIP_V2
]

MODELS_ACPARTNER_MIIO = [
    MODEL_LUMI_ACPARTNER_V3
]

MODELS_MIOT = [
    MODEL_QMI_POWERSTRIP_2A1C1,
    MODEL_QMI_PLUG_TW02
]

MODELS_ALL_DEVICES = MODELS_PLUG_MIIO + MODELS_PLUG_WITH_USB_MIIO + MODELS_POWERSTRIP_MIIO + MODELS_ACPARTNER_MIIO + MODELS_MIOT

DEFAULT_SCAN_INTERVAL = 30
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

ATTR_POWER = "power"
ATTR_TEMPERATURE = "temperature"
ATTR_LOAD_POWER = "load_power"
ATTR_MODEL = "model"
ATTR_POWER_MODE = "power_mode"
ATTR_WIFI_LED = "wifi_led"
ATTR_POWER_PRICE = "power_price"
ATTR_PRICE = "price"
ATTR_WORKING_TIME = "working_time"
ATTR_COUNT_DOWN_TIME = "count_down_time"
ATTR_COUNT_DOWN = "count_down"
ATTR_KEEP_RELAY = "keep_relay"

@dataclass
class XiaomiPlugSensorDescription(
    SensorEntityDescription
):
    """Class to describe an Xiaomi Plug sensor."""


PLUG_SENSORS: tuple[XiaomiPlugSensorDescription, ...] = (
    XiaomiPlugSensorDescription(
        key="power_consumption",
        name="Power consumption",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    XiaomiPlugSensorDescription(
        key="energy",
        name="Energy",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    XiaomiPlugSensorDescription(
        key="load_power",
        name="Power",
        native_unit_of_measurement=POWER_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    XiaomiPlugSensorDescription(
        key="voltage",
        name="Voltage",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    XiaomiPlugSensorDescription(
        key="current",
        name="Current",
        native_unit_of_measurement=ELECTRIC_CURRENT_MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    XiaomiPlugSensorDescription(
        key="remain_time",
        name="Remain Time",
        native_unit_of_measurement=TIME_SECONDS,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:counter"
    ),
    XiaomiPlugSensorDescription(
        key="system_status",
        name="System Status",
        icon="mdi:chip"
    )
)
