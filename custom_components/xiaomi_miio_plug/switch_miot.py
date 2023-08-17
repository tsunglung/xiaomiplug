"""
Support for Xiaomi AirFryer.

"""
import enum
from typing import Any, Dict
import logging
import click

from miio.click_common import command, format_output
from miio.device import DeviceStatus
from miio.miot_device import MiotDevice
from .const import (
    MODEL_QMI_POWERSTRIP_2A1C1,
    MODEL_QMI_PLUG_TW02
)

_LOGGER = logging.getLogger(__name__)


MIOT_MAPPING = {
    # https://home.miot-spec.com/spec?type=urn%3Amiot-spec-v2%3Adevice%3Aoutlet%3A0000A002%3Aqmi-2a1c1%3A1%3A0000C816
    MODEL_QMI_POWERSTRIP_2A1C1: {
        "status": {"siid": 2, "piid": 1},  # read, notify, write
        "mode": {"siid": 2, "piid": 2},  # read, notify, write
        "temperature": {"siid": 2, "piid": 3},  # read, notify
        "working_time": {"siid": 2, "piid": 4},  # read, notify
        "power_consumption": {"siid": 3, "piid": 1},  # read, notify
        "load_power": {"siid": 3, "piid": 2},  # read, notify
        "voltage": {"siid": 3, "piid": 3},  # read, notify
        "current": {"siid": 3, "piid": 4},  # read, notify
        "energy": {"siid": 3, "piid": 5},  # read, notify
        "count_down_time": {"siid": 4, "piid": 1},  # read, notify, write
        "remain_time": {"siid": 4, "piid": 2},  # read, notify
        "enable_count_down": {"siid": 4, "piid": 3},  # read, notify
        "open_time": {"siid": 5, "piid": 1},  # read, notify, write
        "close_time": {"siid": 5, "piid": 2},  # read, notify, write
        "enable_relay_loop": {"siid": 5, "piid": 3},  # read, notify, write
        "enable_led": {"siid": 6, "piid": 1},  # read, notify, write
        "enable_buzzer": {"siid": 6, "piid": 2},  # read, notify, write
        "system_status": {"siid": 6, "piid": 3},  # read, notify
        "keep_relay": {"siid": 6, "piid": 4},  # read, notify, write
        "calibration": {"siid": 7, "piid": 1},  # read, notify, write
    },
    # https://home.miot-spec.com/spec?type=urn:miot-spec-v2:device:outlet:0000A002:qmi-tw02:1
    MODEL_QMI_PLUG_TW02: {
        "on": {"siid": 2, "piid": 1},  # read, notify, write
        "system_status": {"siid": 2, "piid": 3},  # read, notify, write
        "temperature": {"siid": 2, "piid": 6},  # read, notify
        "working_time": {"siid": 2, "piid": 7},  # read, notify
        "power_consumption": {"siid": 4, "piid": 1},  # read, notify
        "current": {"siid": 4, "piid": 2},  # read, notify
        "voltage": {"siid": 4, "piid": 3},  # read, notify
        "load_power": {"siid": 4, "piid": 4},  # read, notify
        "energy": {"siid": 4, "piid": 5},  # read, notify
        "control_locked": {"siid": 5, "piid": 1},  # read, notify, write
        "enable_count_down": {"siid": 6, "piid": 1},  # read, notify, write
        "count_down_time": {"siid": 6, "piid": 2},  # read, notify, write
        "count_down_remain_tm": {"siid": 6, "piid": 3},  # read, notify, write
        "enable_relay_loop": {"siid": 6, "piid": 4},  # read, notify, write
        "loop_relay_close_tm": {"siid": 6, "piid": 5},  # read, notify, write
        "loop_relay_break_tm": {"siid": 6, "piid": 6},  # read, notify, write
        "timer_ifo": {"siid": 6, "piid": 8},  # read, notify, write
        "timer_cfg": {"siid": 6, "piid": 9},  # read, notify, write
        "local_cd_enable": {"siid": 6, "piid": 10},  # read, notify, write
        "local_cd_set_time": {"siid": 6, "piid": 11},  # read, notify, write
        "local_cd_remain_time": {"siid": 6, "piid": 12},  # read, notify, write
        "local_cd_action": {"siid": 6, "piid": 13},  # read, notify, write
        "lowerpower_threshold": {"siid": 7, "piid": 1},  # read, notify, write
        "lowerpower_time": {"siid": 7, "piid": 2},  # read, notify, write
        "lowerpower_enable": {"siid": 7, "piid": 3},  # read, notify, write
        "calibration": {"siid": 8, "piid": 3},  # read, notify, write
    }
}


class DeviceException(Exception):
    """Exception wrapping any communication errors with the device."""


class Status(enum.Enum):
    """ Status """
    Unknown = -1
    Off = 0
    On = 1

class SystemStatus(enum.Enum):
    """ System Status """
    Unknown = -1
    Normal = 0
    Protected_OverCurrent = 1
    Protected_OverTemperature = 2
    Alarm_OverCurrent = 3
    Alarm_OverTemperature = 4


class SwitchStatusMiot(DeviceStatus):
    """Container for status reports for Xiaomi SwitchStatusMiot."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        {
          'id': 1,
          'result': [
            {'did': 'status', 'siid': 2, 'piid': 1, 'code': 0, 'value': 0},
            {'did': 'mode', 'siid': 2, 'piid': 2, 'code': 0, 'value': 0},
            {'did': 'temperature', 'siid': 2, 'piid': 3, 'code': 0, 'value': 0},
            {'did': 'load_power', 'siid': 3, 'piid': 2, 'code': 0, 'value': 0}
          ],
          'exe_time': 280
        }
        """
        self.data = data

    @property
    def is_on(self) -> bool:
        """True if device is currently on."""
        return self.data["status"]

    @property
    def mode(self) -> int:
        """Mode."""
        return self.data.get("mode")

    @property
    def status(self) -> int:
        """Operation status."""
        try:
            return Status(self.data["status"])
        except ValueError:
            _LOGGER.error("Unknown Status (%s)", self.data["status"])
            return Status.Unknown

    @property
    def temperature(self) -> int:
        """Temperature"""
        return self.data["temperature"]

    @property
    def working_time(self) -> int:
        """Working time"""
        return self.data["working_time"]

    @property
    def load_power(self) -> int:
        """Load Power"""
        return self.data["load_power"]

    @property
    def voltage(self) -> int:
        """Voltage"""
        return self.data["voltage"]

    @property
    def current(self) -> int:
        """Current"""
        return self.data["current"]

    @property
    def power_consumption(self) -> int:
        """Power Consumption"""
        return self.data["power_consumption"]

    @property
    def energy(self) -> int:
        """Energy"""
        return self.data["energy"]

    @property
    def count_down_time(self) -> int:
        """Count Down Time"""
        return self.data["count_down_time"]

    @property
    def remain_time(self) -> int:
        """Remain Time"""
        return self.data["remain_time"]

    @property
    def enable_count_down(self) -> int:
        """Enable Count Down"""
        return self.data["enable_count_down"]

    @property
    def open_time(self) -> int:
        """Loop open time"""
        return self.data["open_time"]

    @property
    def close_time(self) -> int:
        """Loop close time"""
        return self.data["close_time"]

    @property
    def enable_relay_loop(self) -> int:
        """Enable relay loop"""
        return self.data["enable_relay_loop"]

    @property
    def wifi_led(self) -> int:
        """LED"""
        return self.data["enable_led"]

    @property
    def buzzer(self) -> int:
        """Buzzer"""
        return self.data["enable_buzzer"]

    @property
    def system_status(self) -> int:
        """System status."""
        try:
            return SystemStatus(self.data["system_status"])
        except ValueError:
            _LOGGER.error("Unknown System Status (%s)", self.data["system_status"])
            return SystemStatus.Unknown

    @property
    def keep_relay(self) -> int:
        """Keep Relay"""
        return self.data["keep_relay"]


class SwitchMiot(MiotDevice):
    """Interface for Plug/PowerStrip Miot"""
    mapping = MIOT_MAPPING[MODEL_QMI_POWERSTRIP_2A1C1]

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_QMI_POWERSTRIP_2A1C1,
    ) -> None:
        if model not in MIOT_MAPPING:
            raise DeviceException("Invalid SwitchMiot model: %s" % model)

        super().__init__(ip, token, start_id, debug, lazy_discover)
        self._model = model

    @command(
        default_output=format_output(
            "",
            "Status: {result.status.name}\n"
        )
    )
    def status(self) -> SwitchStatusMiot:
        """Retrieve properties."""
        return SwitchStatusMiot(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting mode {mode}"),
    )
    def set_power_mode(self, mode: bool):
        """Set power mode."""

        return self.set_property("mode", mode)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Start/Stop count down {mode}"),
    )
    def count_down(self, mode: bool):
        """Start/Stop count down."""

        return self.set_property("enable_count_down", mode)

    @command(
        click.argument("time", type=int),
        default_output=format_output("Setting count down time {time}"),
    )
    def set_count_down_time(self, time: int):
        """Setting count down time. """

        return self.set_property("count_down_time", time)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting Wifi LED {mode}"),
    )
    def set_wifi_led(self, mode: bool):
        """Set Wifi LED."""

        return self.set_property("enable_led", mode)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting Buzzer {mode}"),
    )
    def set_buzzer(self, mode: bool):
        """Set Buzzer."""

        return self.set_property("enable_buzzer", mode)

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Keep Relay {mode}"),
    )
    def set_keep_relay(self, mode: bool):
        """Set keep relay."""

        return self.set_property("keep_relay", mode)

    def on(self):
        return self.set_property("status", True)

    def off(self):
        return self.set_property("status", False)

class SwitchStatusMiotTW02(SwitchStatusMiot):
    """Container for status reports for Xiaomi SwitchStatusMiot."""

    @property
    def is_on(self) -> bool:
        """True if device is currently on."""
        return self.data["on"]

    @property
    def mode(self) -> int:
        """Mode."""
        return self.data.get("on")

    @property
    def remain_time(self) -> int:
        """Remain Time"""
        return self.data["count_down_remain_tm"]

    @property
    def open_time(self) -> int:
        """Loop open time"""
        return self.data["loop_relay_break_tm"]

    @property
    def close_time(self) -> int:
        """Loop close time"""
        return self.data["loop_relay_close_tm"]


class SwitchMiotTW02(SwitchMiot):
    """Interface for Plug Miot TW02"""
    mapping = MIOT_MAPPING[MODEL_QMI_PLUG_TW02]

    @command(
        default_output=format_output(
            "",
            "Status: {result.status.name}\n"
        )
    )
    def status(self) -> SwitchStatusMiotTW02:
        """Retrieve properties."""
        return SwitchStatusMiotTW02(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    @command(
        click.argument("mode", type=bool),
        default_output=format_output("Setting mode {mode}"),
    )
    def set_power_mode(self, mode: bool):
        """Set power mode."""
        return self.set_property("on", mode)

    def on(self):
        return self.set_property("on", True)

    def off(self):
        return self.set_property("on", False)