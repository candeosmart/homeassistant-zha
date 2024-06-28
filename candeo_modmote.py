"""Candeo Modmote devices."""

from __future__ import annotations
from typing import Any, Optional, Union, Final
import logging
from zigpy.zcl import foundation
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.profiles import zha
from zigpy.typing import AddressingMode
from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    Identify,
    LevelControl,
    OnOff,
    Ota,
    PowerConfiguration,
    Scenes,
    Time,
)
from zigpy.zcl.foundation import (
    BaseAttributeDefs,
    BaseCommandDefs,
    ZCLAttributeDef,
    ZCLCommandDef,
)
from zigpy.zcl.clusters.lightlink import LightLink
from zhaquirks.const import (
    BUTTON_1,
    BUTTON_2,
    BUTTON_3,
    BUTTON_4,
    COMMAND,
    DEVICE_TYPE,
    DOUBLE_PRESS,
    ENDPOINT_ID,
    ENDPOINTS,
    INPUT_CLUSTERS,
    LONG_PRESS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    SHORT_PRESS,
    ZHA_SEND_EVENT,
)

import zigpy.types as t

_LOGGER = logging.getLogger(__name__)


class SwitchMode(t.enum8):
    """SwitchMode enum"""

    Command = 0x00
    Event = 0x01


class CandeoModmote(CustomDevice):
    """Candeo Modmote."""

    def __init__(self, *args, **kwargs):
        """__init___"""
        super().__init__(*args, **kwargs)

    class CandeoModmoteCluster(CustomCluster):
        """CandeoModmoteCluster: fire events corresponding to press type."""
        press_type = {
            0x00: SHORT_PRESS,
            0x01: DOUBLE_PRESS,
            0x02: LONG_PRESS,
        }

        cluster_id: Final[t.uint16_t] = 0x0006
        name = "CandeoModmote_Cluster"
        ep_attribute = "CandeoModmote_Cluster"

        class AttributeDefs(BaseAttributeDefs):
            """overwrite AttributeDefs"""
            on_off: Final = ZCLAttributeDef(
                id=0x0000, type=t.Bool, access="rps", mandatory=True
            )
            switch_mode: Final = ZCLAttributeDef(
                id=0x8004, type=SwitchMode, access="rw", mandatory=True
            )
            cluster_revision: Final = foundation.ZCL_CLUSTER_REVISION_ATTR
            reporting_status: Final = foundation.ZCL_REPORTING_STATUS_ATTR

        class ServerCommandDefs(BaseCommandDefs):
            """overwrite ServerCommandDefs"""
            off: Final = ZCLCommandDef(id=0x00, schema={}, direction=False)
            on: Final = ZCLCommandDef(id=0x01, schema={}, direction=False)
            press_type: Final = ZCLCommandDef(
                id=0xFD,
                schema={"press_type": t.uint8_t},
                direction=False,
                is_manufacturer_specific=True,
            )

        event_mode = {0x8004: 0x01}

        def __init__(self, *args, **kwargs):
            """__init___"""
            self.last_tsn = -1
            self.mode = "unknown"
            super().__init__(*args, **kwargs)

        async def bind(self):
            """overwrite bind"""
            self.debug("CandeoModmote: bind called")
            if self.endpoint.endpoint_id == 1:
                self.debug("CandeoModmote: casting tuya spell")
                tuya_spell = [4, 0, 1, 5, 7, 0xFFFE]
                basic_cluster = self.endpoint.device.endpoints[1].in_clusters[
                    Basic.cluster_id
                ]
                await basic_cluster.read_attributes(tuya_spell)
                self.debug("CandeoModmote: attempted to cast tuya spell!")
                self.debug("CandeoModmote: configuring event mode")
                candeomodmote_cluster = self.endpoint.device.endpoints[1].in_clusters[
                    self.cluster_id
                ]
                await candeomodmote_cluster.write_attributes(self.event_mode)
                self.debug("CandeoModmote: attempted to switch device mode!")
            return (foundation.Status.SUCCESS,)

        async def configure_reporting(
            self,
            attribute,
            min_interval,
            max_interval,
            reportable_change,
            manufacturer=None,
        ):
            """overwrite configure_reporting"""
            self.debug("CandeoModmote: configure_reporting called")

        async def _configure_reporting(self, records, *args, **kwargs):
            """overwrite _configure_reporting"""
            self.debug("CandeoModmote: _configure_reporting called")

        def _update_attribute(self, attrid, value):
            """overwrite _update_attribute"""
            self.debug(
                "CandeoModmote: _update_attribute called - attrid: [%s] value: [%s]",
                attrid,
                value,
            )
            if self.endpoint.endpoint_id == 1 and attrid == 32772:
                if value == SwitchMode.Command:
                    self.debug(
                        "CandeoModmote: device is in command mode, reconfiguring it back to \
                        event mode!"
                    )
                    self.mode = "command"
                    self.switch_mode()
                elif value == SwitchMode.Event:
                    self.debug("CandeoModmote: device is in event mode!")
                    self.mode = "event"
                else:
                    super()._update_attribute(attrid, value)
            elif attrid == 0:
                self.debug("CandeoModmote: received on_off - [%s]", value)
                self.check_mode()
            else:
                super()._update_attribute(attrid, value)

        def switch_mode(self):
            """switch device mode"""
            self.debug("CandeoModmote: switch_mode called")
            self.listener_event(ZHA_SEND_EVENT, "switch device mode event", [])
            candeomodmote_cluster = self.endpoint.device.endpoints[1].in_clusters[
                self.cluster_id
            ]
            self.create_catching_task(
                candeomodmote_cluster.write_attributes(self.event_mode)
            )
            self.debug("CandeoModmote: attempted to switch device mode!")

        def check_mode(self):
            """check device mode"""
            self.debug("CandeoModmote: check_mode called")
            if self.mode == "command":
                self.debug(
                    "CandeoModmote: device is flagged as being in command mode, \
                    reconfiguring it back to event mode!"
                )
                self.switch_mode()
            else:
                self.debug(
                    "CandeoModmote: device appears to be in command mode still, based \
                    on receiving on_off command or attribute report, flagging it as in command mode"
                )
                self.mode = "command"
                self.listener_event(ZHA_SEND_EVENT, "read device mode event", [])

        def handle_message(
            self,
            hdr: foundation.ZCLHeader,
            args: list[Any],
            *,
            dst_addressing: AddressingMode | None = None,
        ) -> None:
            """overwrite handle_message to suppress cluster_command events"""
            self.debug(
                "CandeoModmote: Received command 0x%02X (TSN %d): %s",
                hdr.command_id,
                hdr.tsn,
                args,
            )
            if hdr.frame_control.is_cluster:
                self.handle_cluster_request(hdr, args, dst_addressing=dst_addressing)
                return
            self.listener_event("general_command", hdr, args)
            self.handle_cluster_general_request(
                hdr, args, dst_addressing=dst_addressing
            )

        def handle_cluster_request(
            self,
            hdr: foundation.ZCLHeader,
            args: list[Any],
            *,
            dst_addressing: Optional[
                Union[t.Addressing.Group, t.Addressing.IEEE, t.Addressing.NWK]
            ] = None,
        ):
            """overwrite handle_cluster_request to custom process this cluster"""
            self.debug("CandeoModmote: handle_cluster_request called")
            if hdr.tsn == self.last_tsn:
                _LOGGER.debug("CandeoModmote: ignoring duplicate frame from device")
                return
            self.last_tsn = hdr.tsn
            if not hdr.frame_control.disable_default_response:
                self.debug("CandeoModmote: sending default response")
                self.send_default_rsp(hdr, status=foundation.Status.SUCCESS)
            if hdr.command_id == 0xFD:
                press_type = args[0]
                self.debug("CandeoModmote: received press_type - [%s]", press_type)
                event_type = self.press_type.get(press_type, "unknown")
                self.debug("CandeoModmote: received event_type - [%s]", event_type)
                self.listener_event(ZHA_SEND_EVENT, event_type, [])
            elif hdr.command_id == 0x00 or hdr.command_id == 0x01:
                self.debug("CandeoModmote: received on_off - [%s]", hdr.command_id)
                self.check_mode()
            else:
                unknown_command = hdr.command_id
                self.debug("CandeoModmote: received unknown - [%s]", unknown_command)

    signature = {
        # "node_descriptor": "NodeDescriptor(byte1=2, byte2=64, mac_capability_flags=128,
        # manufacturer_code=4098, maximum_buffer_size=82, maximum_incoming_transfer_size=82,
        # server_mask=11264, maximum_outgoing_transfer_size=82, descriptor_capability_field=0,
        # *allocate_address=True, *complex_descriptor_available=False,
        # *is_alternate_pan_coordinator=False, *is_coordinator=False, *is_end_device=True,
        # *is_full_function_device=False, *is_mains_powered=False, *is_receiver_on_when_idle=False,
        # *is_router=False, *is_security_capable=False, *is_valid=True,
        # *logical_type=<LogicalType.EndDevice: 2>, *user_descriptor_available=False)",
        # SizePrefixedSimpleDescriptor(endpoint=1, profile=260, device_type=260, device_version=1,
        # input_clusters=[0, 1, 3, 4, 6, 4096], output_clusters=[25, 10, 3, 4, 5, 6, 8, 4096])
        MODELS_INFO: [
            ("_TZ3000_czuyt8lz", "TS004F"),
            ("_TZ3000_b3mgfu0d", "TS004F"),
        ],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.DIMMER_SWITCH,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    OnOff.cluster_id,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                    Time.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                    LightLink.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.NON_COLOR_CONTROLLER,
                INPUT_CLUSTERS: [CandeoModmoteCluster, Basic.cluster_id],
                OUTPUT_CLUSTERS: [CandeoModmoteCluster, Time.cluster_id],
            },
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.NON_COLOR_CONTROLLER,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [
                    CandeoModmoteCluster,
                ],
            },
            3: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.NON_COLOR_CONTROLLER,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [
                    CandeoModmoteCluster,
                ],
            },
            4: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.NON_COLOR_CONTROLLER,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [
                    CandeoModmoteCluster,
                ],
            },
        },
    }

    device_automation_triggers = {
        (SHORT_PRESS, BUTTON_1): {ENDPOINT_ID: 1, COMMAND: SHORT_PRESS},
        (LONG_PRESS, BUTTON_1): {ENDPOINT_ID: 1, COMMAND: LONG_PRESS},
        (DOUBLE_PRESS, BUTTON_1): {ENDPOINT_ID: 1, COMMAND: DOUBLE_PRESS},
        (SHORT_PRESS, BUTTON_2): {ENDPOINT_ID: 2, COMMAND: SHORT_PRESS},
        (LONG_PRESS, BUTTON_2): {ENDPOINT_ID: 2, COMMAND: LONG_PRESS},
        (DOUBLE_PRESS, BUTTON_2): {ENDPOINT_ID: 2, COMMAND: DOUBLE_PRESS},
        (SHORT_PRESS, BUTTON_3): {ENDPOINT_ID: 3, COMMAND: SHORT_PRESS},
        (LONG_PRESS, BUTTON_3): {ENDPOINT_ID: 3, COMMAND: LONG_PRESS},
        (DOUBLE_PRESS, BUTTON_3): {ENDPOINT_ID: 3, COMMAND: DOUBLE_PRESS},
        (SHORT_PRESS, BUTTON_4): {ENDPOINT_ID: 4, COMMAND: SHORT_PRESS},
        (LONG_PRESS, BUTTON_4): {ENDPOINT_ID: 4, COMMAND: LONG_PRESS},
        (DOUBLE_PRESS, BUTTON_4): {ENDPOINT_ID: 4, COMMAND: DOUBLE_PRESS},
    }
