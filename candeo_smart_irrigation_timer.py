"""Candeo Smart Irrigation Timer."""

from __future__ import annotations

from typing import Final, Optional, Union

import zigpy.types as t
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.tuya import TUYA_MCU_COMMAND, TuyaLocalCluster
from zhaquirks.tuya.mcu import DPToAttributeMapping, TuyaClusterData, TuyaMCUCluster
from zigpy.profiles import zha
from zigpy.quirks import CustomCluster, CustomDevice
from zigpy.zcl import foundation
from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    OnOff,
    Ota,
    PowerConfiguration,
    Scenes,
    Time,
)
from zigpy.zcl.foundation import (
    BaseAttributeDefs,
    BaseCommandDefs,
    ZCLAttributeDef,
    ZCLCommandDef,
)


class _CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster(
    CustomCluster, PowerConfiguration
):
    "_CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster cluster that \
    prevents setting up binding/attribute reports."

    cluster_id: Final[t.uint16_t] = 0x0001
    name: Final = "Power Configuration"
    ep_attribute: Final = "power"

    async def bind(self):
        """Prevent bind."""
        self.debug(
            "_CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster: bind called"
        )
        return (foundation.Status.SUCCESS,)

    async def _configure_reporting(self, *args, **kwargs):
        """Prevent remote configure reporting."""
        self.debug(
            "_CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster: \
            _configure_reporting called"
        )
        return (foundation.ConfigureReportingResponse.deserialize(b"\x00")[0],)

    def _update_attribute(self, attrid, value):
        """overwrite _update_attribute"""
        self.debug(
            "_CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster: \
            _update_attribute called - attrid: [%s] value: [%s]",
            attrid,
            value,
        )
        if (
            attrid == 0x0021
            or attrid == "battery_percentage_remaining"
            or attrid == self.attributes.battery_percentage_remaining
        ):
            self.debug(
                "_CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster: \
                updating battery percentage"
            )
            value = value * 2
            super()._update_attribute(0x0021, value)


class CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster(
    _CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster
):
    "CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster cluster that prevents \
    setting up binding/attribute reports"


class CandeoSmartIrrigationTimerOnOff(OnOff, TuyaLocalCluster):
    """CandeoSmartIrrigationTimerOnOff cluster."""

    class AttributeDefs(BaseAttributeDefs):
        """overwrite AttributeDefs"""

        on_off: Final = ZCLAttributeDef(
            id=0x0000, type=t.Bool, access="rps", mandatory=True
        )
        cluster_revision: Final = foundation.ZCL_CLUSTER_REVISION_ATTR
        reporting_status: Final = foundation.ZCL_REPORTING_STATUS_ATTR

    class ServerCommandDefs(BaseCommandDefs):
        """overwrite ServerCommandDefs"""

        off: Final = ZCLCommandDef(id=0x00, schema={}, direction=False)
        on: Final = ZCLCommandDef(id=0x01, schema={}, direction=False)

    def __init__(self, *args, **kwargs):
        """__init___"""
        super().__init__(*args, **kwargs)

    async def bind(self):
        """overwrite bind"""
        self.debug("CandeoSmartIrrigationTimerOnOff: bind called")
        if self.endpoint.endpoint_id == 1:
            self.debug("CandeoSmartIrrigationTimerOnOff: casting tuya spell")
            tuya_spell = [4, 0, 1, 5, 7, 0xFFFE]
            basic_cluster = self.endpoint.device.endpoints[1].in_clusters[
                Basic.cluster_id
            ]
            await basic_cluster.read_attributes(tuya_spell)
            self.debug("CandeoSmartIrrigationTimerOnOff: attempted to cast tuya spell!")
        return (foundation.Status.SUCCESS,)

    async def configure_reporting(
        self,
        attribute,
        min_interval,
        max_interval,
        reportable_change,
        manufacturer=None,
    ):
        """overwrite configure_reporting"""
        self.debug("CandeoSmartIrrigationTimerOnOff: configure_reporting called")

    async def _configure_reporting(self, records, *args, **kwargs):
        """overwrite _configure_reporting"""
        self.debug("CandeoSmartIrrigationTimerOnOff: _configure_reporting called")

    def _update_attribute(self, attrid, value):
        """overwrite _update_attribute"""
        self.debug(
            "CandeoSmartIrrigationTimerOnOff: _update_attribute called - attrid: [%s] value: [%s]",
            attrid,
            value,
        )
        if attrid == 0:
            self.debug(
                "CandeoSmartIrrigationTimerOnOff: device turned on, setting automatic close timer"
            )
            cluster_data = TuyaClusterData(
                endpoint_id=self.endpoint.endpoint_id,
                cluster_name="CandeoSmartIrrigationTimer_Cluster",
                cluster_attr="timer_timer_remaining",
                attr_value=2147483647,
                expect_reply=True,
                manufacturer=None,
            )
            self.endpoint.device.command_bus.listener_event(
                TUYA_MCU_COMMAND,
                cluster_data,
            )
        super()._update_attribute(attrid, value)

    async def command(
        self,
        command_id: Union[foundation.GeneralCommand, int, t.uint8_t],
        *args,
        manufacturer: Optional[Union[int, t.uint16_t]] = None,
        expect_reply: bool = True,
        tsn: Optional[Union[int, t.uint8_t]] = None,
    ):
        """Override the default Cluster command."""

        self.debug(
            "CandeoSmartIrrigationTimerOnOff: command called - command is %x, arguments are %s",
            command_id,
            args,
        )

        if command_id in (0x0000, 0x0001):
            cluster_data = TuyaClusterData(
                endpoint_id=self.endpoint.endpoint_id,
                cluster_name=self.ep_attribute,
                cluster_attr="on_off",
                attr_value=bool(command_id),
                expect_reply=expect_reply,
                manufacturer=manufacturer,
            )
            self.endpoint.device.command_bus.listener_event(
                TUYA_MCU_COMMAND,
                cluster_data,
            )
            cluster_data = TuyaClusterData(
                endpoint_id=self.endpoint.endpoint_id,
                cluster_name="CandeoSmartIrrigationTimer_Cluster",
                cluster_attr="timer_timer_remaining",
                attr_value=2147483647,
                expect_reply=expect_reply,
                manufacturer=manufacturer,
            )
            self.endpoint.device.command_bus.listener_event(
                TUYA_MCU_COMMAND,
                cluster_data,
            )
            return foundation.GENERAL_COMMANDS[
                foundation.GeneralCommand.Default_Response
            ].schema(command_id=command_id, status=foundation.Status.SUCCESS)

        self.warning("Unsupported command_id: %s", command_id)
        return foundation.GENERAL_COMMANDS[
            foundation.GeneralCommand.Default_Response
        ].schema(command_id=command_id, status=foundation.Status.UNSUP_CLUSTER_COMMAND)


class CandeoSmartIrrigationTimer(CustomDevice):
    """Candeo Smart Irrigation Timer."""

    def __init__(self, *args, **kwargs):
        """__init___"""
        super().__init__(*args, **kwargs)

    class CandeoSmartIrrigationTimerCluster(TuyaMCUCluster):
        """CandeoSmartIrrigationTimerCluster: Control valve and map data points to attributes."""

        name = "CandeoSmartIrrigationTimer_Cluster"
        ep_attribute = "CandeoSmartIrrigationTimer_Cluster"
        attributes = TuyaMCUCluster.attributes.copy()
        attributes.update(
            {
                0xEF01: ("timer_timer_remaining", t.uint32_t, True),
                0xEF02: ("timer_state", t.enum8, True),
                0xEF03: ("last_valve_open_duration", t.uint32_t, True),
                0xEF04: ("water_consumed_l", t.uint32_t, True),
                0xEF05: ("water_consumed_ml", t.uint32_t, True),
                0xEF06: ("weather_delay", t.enum8, True),
            }
        )

        dp_to_attribute: dict[int, DPToAttributeMapping] = {
            1: DPToAttributeMapping(
                CandeoSmartIrrigationTimerOnOff.ep_attribute,
                "on_off",
            ),
            5: DPToAttributeMapping(
                ep_attribute,
                "water_consumed_ml",
            ),
            6: DPToAttributeMapping(
                ep_attribute,
                "water_consumed_l",
            ),
            7: DPToAttributeMapping(
                CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster.ep_attribute,
                "battery_percentage_remaining",
            ),
            10: DPToAttributeMapping(
                ep_attribute,
                "weather_delay",
            ),
            11: DPToAttributeMapping(
                ep_attribute,
                "timer_timer_remaining",
            ),
            12: DPToAttributeMapping(
                ep_attribute,
                "timer_state",
            ),
            15: DPToAttributeMapping(
                ep_attribute,
                "last_valve_open_duration",
            ),
        }

        data_point_handlers = {
            1: "_dp_2_attr_update",
            5: "_dp_2_attr_update",
            6: "_dp_2_attr_update",
            7: "_dp_2_attr_update",
            10: "_dp_2_attr_update",
            11: "_dp_2_attr_update",
            12: "_dp_2_attr_update",
            15: "_dp_2_attr_update",
        }

        def _update_attribute(self, attrid, value):
            """overwrite _update_attribute"""
            self.debug(
                "CandeoSmartIrrigationTimer: _update_attribute called - attrid: [%s] value: [%s]",
                attrid,
                value,
            )
            super()._update_attribute(attrid, value)

    signature = {
        MODELS_INFO: [("_TZE200_81isopgh", "TS0601")],
        # SizePrefixedSimpleDescriptor(endpoint=1, profile=260, device_type=81, device_version=1,
        # input_clusters=[0, 4, 5, 61184], output_clusters=[25, 10])
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    CandeoSmartIrrigationTimerCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            }
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                DEVICE_TYPE: zha.DeviceType.PUMP_CONTROLLER,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    CandeoSmartIrrigationTimerNoBindPowerConfigurationCluster,
                    CandeoSmartIrrigationTimerOnOff,
                    CandeoSmartIrrigationTimerCluster,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id],
            }
        }
    }
