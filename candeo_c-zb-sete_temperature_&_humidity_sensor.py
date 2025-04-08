"""Candeo C-ZB-SETE Temperature & Humidity Sensor."""

from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl.clusters.general import (
    Basic,
    PowerConfiguration,
    Identify,
)
from zigpy.zcl.clusters.measurement import (
    TemperatureMeasurement,
    RelativeHumidity,
)
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)

class CandeoCZBSETETemperatureHumiditySensor(CustomDevice):
    """Candeo C-ZB-SETE Temperature & Humidity Sensor."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-SETE")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    TemperatureMeasurement.cluster_id,
                    RelativeHumidity.cluster_id,
                ],
                OUTPUT_CLUSTERS: [ 
                    Identify.cluster_id,
                ],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    TemperatureMeasurement.cluster_id,
                    RelativeHumidity.cluster_id,
                ],
                OUTPUT_CLUSTERS: [ ],
            },
        },
    }
