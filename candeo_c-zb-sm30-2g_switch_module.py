"""Candeo C-ZB-SM30-2G Switch Module."""

from zigpy.quirks import CustomCluster
from zigpy.quirks.v2 import QuirkBuilder

import zigpy.types as t
from zigpy.zcl.clusters.general import OnOff
from zigpy.zcl.foundation import ZCLAttributeDef
from typing import Final

CANDEO = "Candeo"

class CandeoStartUpOnOff(t.enum8):
    """Candeo StartUpOnOff Cluster."""
    Off = 0x00
    On = 0x01
    PreviousValue = 0xFF

class CandeoTimedOnOffCluster(OnOff, CustomCluster):
    """Candeo TimedOnOff Cluster."""

    StartUpOnOff: Final = CandeoStartUpOnOff

    class AttributeDefs(OnOff.AttributeDefs):
        """Attribute Definitions."""

        start_up_on_off: Final = ZCLAttributeDef(
            id=0x4003, 
            type=CandeoStartUpOnOff, 
            access="rw"
        )
    
    async def on(self):
        """Override ON command to call on_with_timed_off() if non-zero on_time attribute setting."""
        on_time = self._attr_cache.get(self.AttributeDefs.on_time.id) or 0
        if on_time == 0:
            result = await self.command(self.commands_by_name["on"].id)
        else:
            zcl_args = (0x00, on_time, 0x00)
            result = await self.command(
                self.commands_by_name["on_with_timed_off"].id, *zcl_args
            )

        return result 

(
    QuirkBuilder(CANDEO, "C-ZB-SM30-2G")
    .replace_cluster_occurrences(CandeoTimedOnOffCluster)
    .number(
        attribute_name=CandeoTimedOnOffCluster.AttributeDefs.on_time.name,
        cluster_id=CandeoTimedOnOffCluster.cluster_id,
        endpoint_id=1,
        translation_key="automatic_off_time",
        fallback_name="Automatic off time",
        min_value=0,
        max_value=3600,
        multiplier=0.1,
        step=0.1,
        unit="s",
    )
    .number(
        attribute_name=CandeoTimedOnOffCluster.AttributeDefs.on_time.name,
        cluster_id=CandeoTimedOnOffCluster.cluster_id,
        endpoint_id=2,
        translation_key="automatic_off_time",
        fallback_name="Automatic off time",
        min_value=0,
        max_value=3600,
        multiplier=0.1,
        step=0.1,
        unit="s",
    )
    .add_to_registry()
)
