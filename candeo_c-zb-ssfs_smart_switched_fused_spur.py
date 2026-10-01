"""Candeo C-ZB-SSFS Zigbee Smart Switched Fused Spur."""

from typing import Optional

from zigpy.quirks import CustomCluster
from zigpy.quirks.v2 import QuirkBuilder

import zigpy.types as t
from zigpy.zcl.clusters.general import Basic, OnOff
from zigpy.zcl.clusters.homeautomation import ElectricalMeasurement
from zigpy.zcl.clusters.smartenergy import Metering
from zigpy.zcl.foundation import DataTypeId, ZCLAttributeDef

from zhaquirks import LocalDataCluster

from candeo import CANDEO

class CandeoSwitchedFusedSpurElectricalMeasurement(CustomCluster, ElectricalMeasurement):
    """Sets divisor & multiplier attributes missing on the device."""

    _CONSTANT_ATTRIBUTES = {
        ElectricalMeasurement.AttributeDefs.ac_current_divisor.id: 1000,
        ElectricalMeasurement.AttributeDefs.ac_current_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_voltage_divisor.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_voltage_multiplier.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_power_divisor.id: 1,
        ElectricalMeasurement.AttributeDefs.ac_power_multiplier.id: 1,
    }


class CandeoSwitchedFusedSpurMeteringCluster(CustomCluster, Metering):
    """Sets divisor & multiplier attributes missing on the device."""

    _CONSTANT_ATTRIBUTES = {
        Metering.AttributeDefs.multiplier.id: 1,
        Metering.AttributeDefs.divisor.id: 100,
    }


class CandeoEnforceChildLock(t.enum8):
    """Candeo enforce child lock enum."""
    
    disabled = False
    enabled = True


class CandeoChildLock(t.enum8):
    """Candeo child lock enum."""
    
    disabled = False
    enabled = True


class CandeoPowerOnBehaviour(t.enum8):
    """Candeo power on behaviour enum."""
    
    off = 0
    on = 1
    previous = 2


class CandeoSwitchedFusedSpurBasicCluster(Basic, LocalDataCluster):
    """Candeo Basic Cluster."""

    name = "candeo_basic"
    ep_attribute = "candeo_basic"

    class AttributeDefs(Basic.AttributeDefs):
        """Attribute Definitions."""
        
        enforce_child_lock = ZCLAttributeDef(
            id=0x8803,
            type=CandeoEnforceChildLock,
            zcl_type=DataTypeId.bool_,
            access="rw",
            is_manufacturer_specific=True,
        )

    _CONSTANT_ATTRIBUTES = {}

    _VALID_ATTRIBUTES = {        
        AttributeDefs.enforce_child_lock.id,
    }

    attr_config = {        
        AttributeDefs.enforce_child_lock.id: CandeoEnforceChildLock.disabled,
    }

    def __init__(self, *args, **kwargs):
        """__init___."""
        self._configured = False
        super().__init__(*args, **kwargs)

    async def apply_custom_configuration(self, *args, **kwargs):
        """Apply custom configuration to setup preferences."""
        if not self._configured:
            await self.write_attributes(self.attr_config)
            self._configured = True


class CandeoSwitchedFusedSpurTimedOnOffCluster(OnOff, CustomCluster):
    """Candeo TimedOnOff Cluster."""
    
    class AttributeDefs(OnOff.AttributeDefs):
        """Attribute Definitions."""

        child_lock = ZCLAttributeDef(
            id=0x8000,
            type=CandeoChildLock,
            zcl_type=DataTypeId.bool_,
            access="rw",
            is_manufacturer_specific=True,
        )
        power_on_behaviour = ZCLAttributeDef(
            id=0x8002,
            type=CandeoPowerOnBehaviour,
            zcl_type=DataTypeId.enum8,
            access="rw",
            is_manufacturer_specific=True,
        )

    _CONSTANT_ATTRIBUTES = {}

    _VALID_ATTRIBUTES = {
        AttributeDefs.child_lock.id,
        AttributeDefs.power_on_behaviour.id,
    }

    attr_config = {
        AttributeDefs.child_lock.id: CandeoChildLock.disabled,
        AttributeDefs.power_on_behaviour.id: CandeoPowerOnBehaviour.off,
    }

    def __init__(self, *args, **kwargs):
        """__init___."""
        self._configured = False
        self._enforce_child_lock: Optional[CandeoEnforceChildLock] = None
        super().__init__(*args, **kwargs)

    async def apply_custom_configuration(self, *args, **kwargs):
        """Apply custom configuration to setup preferences."""
        if not self._configured:
            await self.write_attributes(self.attr_config)
            self._configured = True

    async def on(self):
        """Override ON command to call on_with_timed_off() if non-zero on_time attribute setting and to enforce child lock if required."""
        self.get_preferences()
        result = await self.command(self.commands_by_name["on"].id)
        on_delay = self._attr_cache.get(self.AttributeDefs.on_time.id, 0)
        if on_delay != 0:
            zcl_args = (0x00, on_delay, 0x00)
            await self.command(
                self.commands_by_name["on_with_timed_off"].id, *zcl_args
            )
        if self._enforce_child_lock == CandeoEnforceChildLock.enabled:
            await self.write_attributes({
                self.AttributeDefs.child_lock.id: CandeoChildLock.enabled
            })
        await self.read_attributes([self.AttributeDefs.child_lock.id])
        return result     
    
    async def off(self):
        """Override OFF command to enforce child lock if required."""
        self.get_preferences()
        result = await self.command(self.commands_by_name["off"].id)
        if self._enforce_child_lock == CandeoEnforceChildLock.enabled:
            await self.write_attributes({
                self.AttributeDefs.child_lock.id: CandeoChildLock.enabled
            })

        await self.read_attributes([self.AttributeDefs.child_lock.id])
        return result
    
    def get_preferences(self):
        """Get saved preferences from the basic cluster."""
        cluster = self.endpoint.in_clusters.get(CandeoSwitchedFusedSpurBasicCluster.cluster_id)
        if cluster is None:
            return
        self._enforce_child_lock = (
            cluster._attr_cache.get(CandeoSwitchedFusedSpurBasicCluster.AttributeDefs.enforce_child_lock.id, CandeoEnforceChildLock.disabled)
        )


(
    QuirkBuilder(CANDEO, "C-ZB-SSFS")
    .applies_to("TS011F", "_TZ3210_7p3jvwkp")
    .replace_cluster_occurrences(CandeoSwitchedFusedSpurBasicCluster)
    .replace_cluster_occurrences(CandeoSwitchedFusedSpurTimedOnOffCluster)
    .replace_cluster_occurrences(CandeoSwitchedFusedSpurElectricalMeasurement)
    .replace_cluster_occurrences(CandeoSwitchedFusedSpurMeteringCluster)
    .number(
        attribute_name=CandeoSwitchedFusedSpurTimedOnOffCluster.AttributeDefs.on_time.name,
        cluster_id=CandeoSwitchedFusedSpurTimedOnOffCluster.cluster_id,
        endpoint_id=1,
        translation_key="automatic_off_delay",
        fallback_name="Automatic off delay",
        min_value=0,
        max_value=43200,
        multiplier=1,
        step=1,
        unit="s",
    )
    .enum(
        attribute_name=CandeoSwitchedFusedSpurTimedOnOffCluster.AttributeDefs.child_lock.name,
        cluster_id=CandeoSwitchedFusedSpurTimedOnOffCluster.cluster_id,
        endpoint_id=1,
        translation_key="child_lock",
        fallback_name="Child lock",
        enum_class=CandeoChildLock,
    )
    .enum(
        attribute_name=CandeoSwitchedFusedSpurTimedOnOffCluster.AttributeDefs.power_on_behaviour.name,
        cluster_id=CandeoSwitchedFusedSpurTimedOnOffCluster.cluster_id,
        endpoint_id=1,
        translation_key="power_on_behaviour",
        fallback_name="Power on behaviour",
        enum_class=CandeoPowerOnBehaviour,
    )
    .enum(
        attribute_name=CandeoSwitchedFusedSpurBasicCluster.AttributeDefs.enforce_child_lock.name,
        cluster_id=CandeoSwitchedFusedSpurBasicCluster.cluster_id,
        endpoint_id=1,
        translation_key="enforce_child_lock",
        fallback_name="Enforce child lock",
        enum_class=CandeoEnforceChildLock,
    )
    .add_to_registry()
)
