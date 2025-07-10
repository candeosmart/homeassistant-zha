"""Candeo C-ZB-SEMO Motion Sensor."""

import math
from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl.clusters.general import (
    Basic,
    PowerConfiguration,
    Identify,
)
from zigpy.zcl.clusters.measurement import (
    IlluminanceMeasurement,
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

    _CONSTANT_ATTRIBUTES = {ZONE_TYPE: IasZone.ZoneType.Motion_Sensor}

class CandeoIlluminanceMeasurementCluster(IlluminanceMeasurement, CustomCluster):
    """Candeo Illuminance Measurement Cluster."""

    def _update_attribute(self, attrid, value):
        if attrid == self.AttributeDefs.measured_value.id:
            value = pow(10, ((value - 1) / 10000))
            value = self.lux_calibration(value)
            value = 10000 * math.log10(value) + 1
            value = round(value)
        super()._update_attribute(attrid, value)

    @staticmethod
    def lux_calibration(value):
        """Calibrate lux reading from device."""
        lux_value = 1
        if 0 < value <= 2200:
            lux_value = -7.969192 + (0.0151988 * value)
        elif 2200 < value <= 2500:
            lux_value = -1069.189434 + (0.4950663 * value)
        elif value > 2500:
            lux_value = (78029.21628 - (61.73575 * value)) + (0.01223567 * (value**2))
        lux_value = max(lux_value, 1)
        return lux_value

class CandeoCZBSEMOMotionSensor(CustomDevice):
    """Candeo C-ZB-SEMO Motion Sensor."""

    signature = {
        MODELS_INFO: [("Candeo", "C-ZB-SEMO")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.IAS_ZONE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    IlluminanceMeasurement.cluster_id,
                    IasZone.cluster_id,
                ],
                OUTPUT_CLUSTERS: [ ],
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
                    CandeoIlluminanceMeasurementCluster,
                    CandeoIasZone,
                ],
                OUTPUT_CLUSTERS: [ ],
            },
        },
    }
