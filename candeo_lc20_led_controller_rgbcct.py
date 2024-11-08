"""Candeo LC20 LED Controller (C-ZB-LC20-RGBCCT)."""

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

class CandeoRGBCCTOnOffCluster(CustomCluster, OnOff):
    """Candeo RGBCCT Lighting custom cluster."""

    def _update_attribute(self, attrid, value):
        """Read Color Temperature After Any Attribute Report."""
        self.debug(
            "CandeoRGBCCTOnOffCluster: \
            _update_attribute called"
        )        

        color_cluster = self.endpoint.device.endpoints[11].in_clusters[ Color.cluster_id ]
        self.create_catching_task(
            color_cluster.read_attributes([7])
        )
        
        super()._update_attribute(attrid, value) 

class CandeoRGBCCTLevelControlCluster(CustomCluster, LevelControl):
    """Candeo RGBCCT Lighting custom cluster."""

    def _update_attribute(self, attrid, value):
        """Read Color Temperature After Any Attribute Report."""
        self.debug(
            "CandeoRGBCCTLevelControlCluster: \
            _update_attribute called"
        )  

        color_cluster = self.endpoint.device.endpoints[11].in_clusters[ Color.cluster_id ]
        self.create_catching_task(
            color_cluster.read_attributes([7])
        )
        
        super()._update_attribute(attrid, value)

class CandeoRGBCCTColorCluster(CustomCluster, Color):
    """Candeo RGBCCT Lighting custom cluster."""

    async def _configure_reporting(self, records, *args, **kwargs):
        """Only configure reporting for Color XY."""
        self.debug(
            "CandeoRGBCCTColorCluster: \
            _configure_reporting called"
        )        
        newrecords = records.copy()
        for record in newrecords:
            if record.attrid in (0x0007, "color_temperature",):
                self.debug(
                    "CandeoRGBCCTColorCluster: \
                    skipping - attrid: [%s]",
                    record.attrid
                )
                records.remove(record)
        
        return await super()._configure_reporting(records, *args, **kwargs)

class CandeoLC20LEDControllerRGBCCT(CustomDevice):
    """Candeo LC20 LED Controller (C-ZB-LC20-RGBCCT)."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-LC20-RGBCCT")],
        ENDPOINTS: {
            11: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.EXTENDED_COLOR_LIGHT,
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
                    CandeoRGBCCTOnOffCluster,
                    CandeoRGBCCTLevelControlCluster,
                    CandeoRGBCCTColorCluster,
                    LightLink.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Ota.cluster_id,
                ],
            },
        },
    }
