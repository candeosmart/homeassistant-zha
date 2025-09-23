"""Candeo C-ZB-RD1P Rotary Dimmer Pro (Remote Mode)."""

from typing import Final
from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl.clusters.general import (
    Basic,
    Identify,
    LevelControl,
    MoveMode,
    StepMode,
    OnOff,
    Ota,
)
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zigpy.zcl.clusters.lightlink import LightLink
from zigpy.zcl.clusters.smartenergy import Metering

from zigpy.zcl.foundation import (
    BaseCommandDefs,
    Direction,
    ZCLCommandDef,
)

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    COMMAND,
    CLUSTER_ID,
    ENDPOINT_ID,
    PARAMS,
)

COMMAND_PRESS = "press"
COMMAND_DOUBLE_PRESS = "double_press"
COMMAND_HOLD = "hold"
COMMAND_RELEASE = "release"
COMMAND_STARTED_ROTATING = "started_rotating"
COMMAND_CONTINUED_ROTATING = "continued_rotating"
COMMAND_STOPPED_ROTATING = "stopped_rotating"

class CandeoCZBRD1PRotaryDimmerProRemoteMode(CustomDevice):
    """Candeo C-ZB-RD1P Rotary Dimmer Pro (Remote Mode)."""    

    class CandeoOnOffCluster(OnOff, CustomCluster):
        """Candeo OnOff Cluster."""        

        class ServerCommandDefs(BaseCommandDefs):
            """overwrite ServerCommandDefs."""
            double_press: Final = ZCLCommandDef(
                id=0x00, 
                schema={}, 
                direction=Direction.Client_to_Server
            )
            press: Final = ZCLCommandDef(
                id=0x01, 
                schema={}, 
                direction=Direction.Client_to_Server
            )
            hold: Final = ZCLCommandDef(
                id=0x02, 
                schema={}, 
                direction=Direction.Client_to_Server
            )
            release: Final = ZCLCommandDef(
                id=0x03, 
                schema={}, 
                direction=Direction.Client_to_Server
            )
    
    class CandeoLevelControlCluster(LevelControl, CustomCluster):
        """Candeo LevelControl Cluster."""        

        class ServerCommandDefs(BaseCommandDefs):
            """overwrite ServerCommandDefs."""
            started_rotating: Final = ZCLCommandDef(
                id=0x05,
                schema={"direction": MoveMode},
                direction=Direction.Client_to_Server,
            )
            continued_rotating: Final = ZCLCommandDef(
                id=0x06,
                schema={"direction": StepMode},
                direction=Direction.Client_to_Server,
            )
            stopped_rotating: Final = ZCLCommandDef(
                id=0x03,
                schema={},
                direction=Direction.Client_to_Server,
            )

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-RD1P-REM")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.DIMMABLE_LIGHT,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Metering.cluster_id,
                    ElectricalMeasurement.cluster_id,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Identify.cluster_id,
                    Ota.cluster_id,
                ],
            },
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.REMOTE_CONTROL,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Identify.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.METER_INTERFACE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Metering.cluster_id,
                    ElectricalMeasurement.cluster_id,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [ ],
            },
            2: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.REMOTE_CONTROL,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    CandeoOnOffCluster,
                    CandeoLevelControlCluster,
                ],
            },
        },
    }

    device_automation_triggers = {
        ("Pressed", "Rotary knob"): {COMMAND: COMMAND_PRESS, CLUSTER_ID: 6, ENDPOINT_ID: 2},
        ("Double pressed", "Rotary knob"): {COMMAND: COMMAND_DOUBLE_PRESS, CLUSTER_ID: 6, ENDPOINT_ID: 2},
        ("Held", "Rotary knob"): {COMMAND: COMMAND_HOLD, CLUSTER_ID: 6, ENDPOINT_ID: 2},
        ("Released", "Rotary knob"): {COMMAND: COMMAND_RELEASE, CLUSTER_ID: 6, ENDPOINT_ID: 2},
        ("Started rotating left", "Rotary knob"): {COMMAND: COMMAND_STARTED_ROTATING, CLUSTER_ID: 8, ENDPOINT_ID: 2, PARAMS: {"direction": 1}},
        ("Rotating left", "Rotary knob"): {COMMAND: COMMAND_CONTINUED_ROTATING, CLUSTER_ID: 8, ENDPOINT_ID: 2, PARAMS: {"direction": 1}},
        ("Started rotating right", "Rotary knob"): {COMMAND: COMMAND_STARTED_ROTATING, CLUSTER_ID: 8, ENDPOINT_ID: 2, PARAMS: {"direction": 0}},
        ("Rotating right", "Rotary knob"): {COMMAND: COMMAND_CONTINUED_ROTATING, CLUSTER_ID: 8, ENDPOINT_ID: 2, PARAMS: {"direction": 0}},
        ("Stopped rotating", "Rotary knob"): {COMMAND: COMMAND_STOPPED_ROTATING, CLUSTER_ID: 8, ENDPOINT_ID: 2},
    }
