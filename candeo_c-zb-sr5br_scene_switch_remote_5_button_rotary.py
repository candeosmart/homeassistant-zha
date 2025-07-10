"""Candeo C-ZB-SR5BR Scene Switch Remote - 5 Button Rotary."""

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
)
from zigpy.zcl.foundation import (
    BaseCommandDefs,
    ZCLCommandDef,
)
from zigpy.zcl.clusters.lightlink import LightLink
from zigpy.zcl.clusters.homeautomation import Diagnostic
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    ENDPOINT_ID,
    COMMAND,
    ZHA_SEND_EVENT,
)
import zigpy.types as t

class CandeoCZBSR5BRSceneSwitchRemote(CustomDevice):
    """Candeo C-ZB-SR5BR Scene Switch Remote - 5 Button Rotary."""

    class CandeoCZBSR5BRSceneSwitchRemoteCluster(CustomCluster):
        """CandeoCZBSR5BRSceneSwitchRemoteCluster: fire events corresponding to button press or ring rotation."""
        message_types = {
            0x01: "button_press",
            0x03: "ring_rotation",
        }

        button_numbers = {
            0x01: "button_1_",
            0x02: "button_2_",
            0x04: "button_3_",
            0x08: "button_4_",
            0x10: "centre_button_",
        }

        button_actions = {
            0x01: "click",
            0x02: "double_click",
            0x03: "hold",
            0x04: "release",
        }

        ring_directions = {
            0x01: "rotating_right",
            0x02: "rotating_left",
        }

        ring_actions = {
            0x01: "started_",
            0x02: "stopped_",
            0x03: "continued_",
        }

        cluster_id: Final[t.uint16_t] = 0xFF03
        name = "CandeoCZBSR5BRSceneSwitchRemote_Cluster"
        ep_attribute = "CandeoCZBSR5BRSceneSwitchRemoteCluster_Cluster"

        class CandeoCZBSR5BRSSceneSwitchRemoteCommand(t.Struct):
            """CandeoCZBSR5BRSSceneSwitchRemoteCommand: incoming data."""
            field_1: t.uint8_t
            field_2: t.uint8_t
            field_3: t.uint8_t
            field_4: t.uint8_t

        class ServerCommandDefs(BaseCommandDefs):
            """overwrite ServerCommandDefs."""            
            candeo_scene_switch_remote: Final = ZCLCommandDef(
                id=0x01,
                schema={"field_1": t.uint8_t, "field_2": t.uint8_t, "field_3": t.uint8_t, "field_4": t.uint8_t},
                direction=False,
                is_manufacturer_specific=True,
            )

        def __init__(
            self, 
            *args, 
            **kwargs
        ):
            """__init___"""
            self.last_tsn = -1
            self.previous_direction = "unknown"
            self.previous_rotation_event = "unknown"
            super().__init__(*args, **kwargs)

        def handle_message(
            self,
            hdr: foundation.ZCLHeader,
            args: list[Any],
            *,
            dst_addressing: AddressingMode | None = None,
        ) -> None:
            """overwrite handle_message to suppress cluster_command events."""
            self.debug(
                "CandeoCZBSR5BRSceneSwitchRemote: Received command 0x%02X (TSN %d): %s",
                hdr.command_id,
                hdr.tsn,
                args,
            )
            if hdr.frame_control.is_cluster:
                self.handle_cluster_request(hdr, args, dst_addressing=dst_addressing)
                return

        def handle_cluster_request(
            self,
            hdr: foundation.ZCLHeader,
            args: tuple[CandeoCZBSR5BRSSceneSwitchRemoteCommand],
            *,
            dst_addressing: Optional[
                Union[t.Addressing.Group, t.Addressing.IEEE, t.Addressing.NWK]
            ] = None,
        ):
            """overwrite handle_cluster_request to custom process this cluster."""
            self.debug("CandeoCZBSR5BRSceneSwitchRemote: handle_cluster_request called")
            if hdr.tsn == self.last_tsn:
                self.debug("CandeoCZBSR5BRSceneSwitchRemote: ignoring duplicate frame from device")
                return
            self.last_tsn = hdr.tsn
            if not hdr.frame_control.disable_default_response:
                self.debug("CandeoCZBSR5BRSceneSwitchRemote: sending default response")
                self.send_default_rsp(hdr, status=foundation.Status.SUCCESS)
            if hdr.command_id == self.ServerCommandDefs.candeo_scene_switch_remote.id:
                if args.field_1 is None or args.field_2 is None or args.field_3 is None or args.field_4 is None:
                    return
                self.debug("CandeoCZBSR5BRSceneSwitchRemote: received field_1 - [%s] field_2 - [%s] field_3 - [%s] field_4 - [%s]", args.field_1, args.field_2, args.field_3, args.field_4)
                message_type = self.message_types.get(args.field_1, "unknown")
                if message_type == "button_press":
                    button_number = self.button_numbers.get(args.field_3, "unknown")
                    button_action = self.button_actions.get(args.field_4, "unknown")
                    self.debug("CandeoCZBSR5BRSceneSwitchRemote: button_number - [%s] button_action - [%s]", button_number, button_action)
                    if button_number != "unknown" and button_action != "unknown":
                        self.listener_event(ZHA_SEND_EVENT, button_number + button_action, [])
                elif message_type == "ring_rotation":
                    ring_action = self.ring_actions.get(args.field_3, "unknown")
                    self.debug("CandeoCZBSR5BRSceneSwitchRemote: ring_action - [%s]", ring_action)
                    if ring_action != "unknown":
                        if ring_action == "stopped_":
                            self.debug("CandeoCZBSR5BRSceneSwitchRemote: previous_direction - [%s]", self.previous_direction)
                            if self.previous_direction != "unknown":
                                self.debug("CandeoCZBSR5BRSceneSwitchRemote: added event for stopped_[%s]", self.previous_direction)
                                self.listener_event(ZHA_SEND_EVENT, "stopped_" + self.previous_direction, [])
                            self.previous_rotation_event = "stopped_"
                        else:
                            ring_direction = self.ring_directions.get(args.field_2, "unknown")
                            if ring_direction != "unknown":
                                self.debug("CandeoCZBSR5BRSceneSwitchRemote: previous_rotation_event - [%s]", self.previous_rotation_event)
                                if self.previous_rotation_event != "unknown":
                                    ring_clicks = args.field_4
                                    if self.previous_rotation_event == "stopped_":
                                        self.debug("CandeoCZBSR5BRSceneSwitchRemote: added initial event for ring_action - started_ ring_direction - [%s]", ring_direction)
                                        self.listener_event(ZHA_SEND_EVENT, "started_" + ring_direction, [])
                                        self.previous_rotation_event = "started_"
                                        if ring_clicks > 1:
                                            for x in range(1, ring_clicks):
                                                self.debug("CandeoCZBSR5BRSceneSwitchRemote: added [%s] extra event for ring_action - continued_ ring_direction - [%s]", x, ring_direction)
                                                self.listener_event(ZHA_SEND_EVENT, "continued_" + ring_direction, [])
                                            self.previous_rotation_event = "continued_"
                                    elif self.previous_rotation_event == "started_" or self.previous_rotation_event == "continued_":
                                        self.debug("CandeoCZBSR5BRSceneSwitchRemote: added initial event for ring_action - continued_ ring_direction - [%s]", ring_direction)
                                        self.listener_event(ZHA_SEND_EVENT, "continued_" + ring_direction, [])
                                        if ring_clicks > 1:
                                            for x in range(1, ring_clicks):
                                                self.debug("CandeoCZBSR5BRSceneSwitchRemote: added [%s] extra event for ring_action - continued_ ring_direction - [%s]", x, ring_direction)
                                                self.listener_event(ZHA_SEND_EVENT, "continued_" + ring_direction, [])
                                        self.previous_rotation_event = "continued_"
                                self.previous_direction = ring_direction
                return
            else:
                unknown_command = hdr.command_id
                self.debug("CandeoCZBSR5BRSceneSwitchRemote: received unknown - [%s]", unknown_command)

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-SR5BR")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.LEVEL_CONTROL_SWITCH,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    Diagnostic.cluster_id,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [                    
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                    Ota.cluster_id,
                    LightLink.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.REMOTE_CONTROL,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Diagnostic.cluster_id,
                    CandeoCZBSR5BRSceneSwitchRemoteCluster,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }

    device_automation_triggers = {
        ("Pressed", "Button 1"): {ENDPOINT_ID: 1, COMMAND: "button_1_click"},
        ("Double Pressed", "Button 1"): {ENDPOINT_ID: 1, COMMAND: "button_1_double_click"},
        ("Held", "Button 1"): {ENDPOINT_ID: 1, COMMAND: "button_1_hold"},
        ("Released", "Button 1"): {ENDPOINT_ID: 1, COMMAND: "button_1_release"},
        ("Pressed", "Button 2"): {ENDPOINT_ID: 1, COMMAND: "button_2_click"},
        ("Double Pressed", "Button 2"): {ENDPOINT_ID: 1, COMMAND: "button_2_double_click"},
        ("Held", "Button 2"): {ENDPOINT_ID: 1, COMMAND: "button_2_hold"},
        ("Released", "Button 2"): {ENDPOINT_ID: 1, COMMAND: "button_2_release"},
        ("Pressed", "Button 3"): {ENDPOINT_ID: 1, COMMAND: "button_3_click"},
        ("Double Pressed", "Button 3"): {ENDPOINT_ID: 1, COMMAND: "button_3_double_click"},
        ("Held", "Button 3"): {ENDPOINT_ID: 1, COMMAND: "button_3_hold"},
        ("Released", "Button 3"): {ENDPOINT_ID: 1, COMMAND: "button_3_release"},
        ("Pressed", "Button 4"): {ENDPOINT_ID: 1, COMMAND: "button_4_click"},
        ("Double Pressed", "Button 4"): {ENDPOINT_ID: 1, COMMAND: "button_4_double_click"},
        ("Held", "Button 4"): {ENDPOINT_ID: 1, COMMAND: "button_4_hold"},
        ("Released", "Button 4"): {ENDPOINT_ID: 1, COMMAND: "button_4_release"},
        ("Pressed", "Centre Button"): {ENDPOINT_ID: 1, COMMAND: "centre_button_click"},
        ("Double Pressed", "Centre Button"): {ENDPOINT_ID: 1, COMMAND: "centre_button_double_click"},
        ("Held", "Centre Button"): {ENDPOINT_ID: 1, COMMAND: "centre_button_hold"},
        ("Released", "Centre Button"): {ENDPOINT_ID: 1, COMMAND: "centre_button_release"},
        ("Started Rotating Left", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "started_rotating_left"},
        ("Continued Rotating Left", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "continued_rotating_left"},
        ("Stopped Rotating Left", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "stopped_rotating_left"},
        ("Started Rotating Right", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "started_rotating_right"},
        ("Continued Rotating Right", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "continued_rotating_right"},
        ("Stopped Rotating Right", "Rotary Ring"): {ENDPOINT_ID: 1, COMMAND: "stopped_rotating_right"},
    }
