"""Candeo C-ZB-SEWA Water Sensor."""

from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl.clusters.general import (
    Basic,
    PowerConfiguration,
    Identify,
    Time,
)
from zigpy.zcl.clusters.security import IasZone
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    ZONE_TYPE,
)

class CandeoIasZone(CustomCluster, IasZone):
    """Candeo IasZone cluster."""

    _CONSTANT_ATTRIBUTES = {ZONE_TYPE: IasZone.ZoneType.Water_Sensor}

class CandeoCZBSEWAWaterSensor(CustomDevice):
    """Candeo C-ZB-SEWA Water Sensor."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-SEWA")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.IAS_ZONE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    IasZone.cluster_id,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.IAS_ZONE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    CandeoIasZone,
                ],
                OUTPUT_CLUSTERS: [
                    Time.cluster_id,
                ],
            },
        },
    }
