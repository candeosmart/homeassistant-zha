"""Candeo LC20 LED Controller (C-ZB-LC20-RGB)."""

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

class CandeoRGBColorCluster(CustomCluster, Color):
    """Candeo RGB Lighting custom cluster."""

    """Only present RGB Color control."""
    _CONSTANT_ATTRIBUTES = {
        Color.AttributeDefs.color_capabilities.id: Color.ColorCapabilities.XY_attributes
    }

    async def _configure_reporting(self, records, *args, **kwargs):
        """Only configure reporting for Color XY."""
        self.debug(
            "CandeoRGBColorCluster: \
            _configure_reporting called"
        )        
        newrecords = records.copy()
        for record in newrecords:
            if record.attrid in (0x0007, "color_temperature",):
                self.debug(
                    "CandeoRGBColorCluster: \
                    skipping - attrid: [%s]",
                    record.attrid
                )
                records.remove(record)
        
        return await super()._configure_reporting(records, *args, **kwargs)

class CandeoLC20LEDControllerRGB(CustomDevice):
    """Candeo LC20 LED Controller (C-ZB-LC20-RGB)."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-LC20-RGB")],
        ENDPOINTS: {
            11: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT,
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
                DEVICE_TYPE: zha.DeviceType.COLOR_DIMMABLE_LIGHT,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    OnOff.cluster_id,
                    LevelControl.cluster_id,
                    CandeoRGBColorCluster,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }
