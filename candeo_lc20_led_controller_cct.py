"""Candeo LC20 LED Controller (C-ZB-LC20-CCT)."""

from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl import foundation
from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    Identify,
    LevelControl,
    OnOff,
    Ota,
    Scenes,
)
from zigpy.zcl.clusters.lighting import Color
from zigpy.zcl.clusters.lightlink import LightLink

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

class CandeoCCTColorCluster(CustomCluster, Color):
    """Candeo CCT Lighting custom cluster."""
    async def _configure_reporting(self, records, *args, **kwargs):
        """Only configure reporting for Color Temperature."""
        self.debug(
            "CandeoCCTColorCluster: \
            _configure_reporting called"
        )        
        newrecords = records.copy()
        for record in newrecords:
            if record.attrid in (0x0003, "current_x", 0x0004, "current_y"):
                self.debug(
                    "CandeoCCTColorCluster: \
                    skipping - attrid: [%s]",
                    record.attrid
                )
                records.remove(record)
        
        return await super()._configure_reporting(records, *args, **kwargs)

class CandeoLC20LEDControllerCCT(CustomDevice):
    """Candeo LC20 LED Controller (C-ZB-LC20-CCT)."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-LC20-CCT")],
        ENDPOINTS: {
            11: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COLOR_TEMPERATURE_LIGHT,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                    Color.cluster_id,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            11: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COLOR_TEMPERATURE_LIGHT,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                    CandeoCCTColorCluster,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }
