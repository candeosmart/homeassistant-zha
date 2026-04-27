"""Candeo c-rfzb-hub kinetic rf to zigbee gateway."""
import asyncio

from zigpy.quirks.v2 import QuirkBuilder
from zigpy.zcl.clusters.general import Identify, OnOff, Basic, Groups, Scenes
from zhaquirks import LocalDataCluster

import zigpy.types as t

from zigpy.zcl.foundation import DataTypeId, ZCLAttributeDef

from candeo import (
    CANDEO,
)

from zhaquirks.const import (
    BUTTON_1,
    BUTTON_2,
    BUTTON_3,
    BUTTON_4,
    BUTTON_5,
    BUTTON_6,
    BUTTON_7,
    BUTTON_8,
    COMMAND,
    COMMAND_DOUBLE,
    COMMAND_TRIPLE,
    COMMAND_QUAD,
    COMMAND_PRESS,
    ENDPOINT_ID,
    SHORT_PRESS,
    DOUBLE_PRESS,
    TRIPLE_PRESS,
    QUADRUPLE_PRESS,
    QUINTUPLE_PRESS,
    ZHA_SEND_EVENT,
)

BUTTON_9 = "button_9"
BUTTON_10 = "button_10"
COMMAND_QUIN = "quintuple"

def generate_device_automation_triggers(ep_ids):
    """Generate automation triggers."""
    ACTION_TO_COMMAND = {
        SHORT_PRESS: COMMAND_PRESS,
        DOUBLE_PRESS: COMMAND_DOUBLE,
        TRIPLE_PRESS: COMMAND_TRIPLE,
        QUADRUPLE_PRESS: COMMAND_QUAD,
        QUINTUPLE_PRESS: COMMAND_QUIN,
    }
    triggers = {}
    for ep_id in ep_ids:
        button_constant_name = f"BUTTON_{ep_id}"
        button_name = globals().get(button_constant_name)
        if button_name is None:
            raise ValueError(f"Button constant {button_constant_name} is not defined")
        for action, command in ACTION_TO_COMMAND.items():
            triggers[(action, button_name)] = {
                ENDPOINT_ID: ep_id,
                COMMAND: command,
            }
    return triggers

def generate_enums(enum_attributes, ep_id):
    """Generate enums for configuration preferences."""
    for attribute_name, enum_class, cluster_id in enum_attributes:
        yield {
            "attribute_name": attribute_name,
            "enum_class": enum_class,
            "cluster_id": cluster_id,
            "endpoint_id": ep_id,
            "unique_id_suffix": f"button_{ep_id}_{attribute_name}_",
            "translation_key": f"button_{ep_id}_{attribute_name}",
            "fallback_name": f"Button {ep_id} {attribute_name.replace('_', ' ')}",
        }

def quirk_setup(quirk_base, endpoints):
    """Dynamically build the quirk to suit the device variant."""
    CLUSTERS_TO_REMOVE = [
        Identify.cluster_id, 
        Groups.cluster_id, 
        Scenes.cluster_id
    ]
    ENUM_ATTRIBUTES = [
        (CandeoBasicCluster.AttributeDefs.actions_detection.name, CandeoActionsDetection, CandeoBasicCluster.cluster_id),
        (CandeoBasicCluster.AttributeDefs.actions_window.name, CandeoActionsWindow, CandeoBasicCluster.cluster_id)
    ]
    quirk = quirk_base.clone()
    ep_ids = list(range(1, endpoints + 1))
    quirk.device_automation_triggers(generate_device_automation_triggers(ep_ids))
    for ep_id in ep_ids:
        for enum_kwargs in generate_enums(ENUM_ATTRIBUTES, ep_id):
            quirk.enum(**enum_kwargs)        
        for cluster_id in CLUSTERS_TO_REMOVE:
            quirk.removes(cluster_id=cluster_id, endpoint_id=ep_id)
        quirk.prevent_default_entity_creation(endpoint_id=ep_id, cluster_id=CandeoOnOffCluster.cluster_id)
    return quirk


class CandeoActionsDetection(t.enum8):
    """Candeo actions detection enum."""

    single = 1
    single_double = 2
    single_double_triple = 3
    single_double_triple_quadruple = 4
    single_double_triple_quadruple_quintuple = 5


class CandeoActionsWindow(t.enum16):
    """Candeo actions window enum."""

    wait_500_ms = 500
    wait_550_ms = 550
    wait_600_ms = 600
    wait_650_ms = 650
    wait_700_ms = 700
    wait_750_ms = 750
    wait_800_ms = 800
    wait_850_ms = 850
    wait_900_ms = 900
    wait_950_ms = 950
    wait_1000_ms = 1000
    wait_1500_ms = 1500
    wait_2000_ms = 2000
    wait_2500_ms = 2500
    wait_3000_ms = 3000


class CandeoButtonActions(t.enum8):
    """Candeo button actions enum."""

    press = 1
    double = 2
    triple = 3
    quadruple = 4
    quintuple = 5  


class CandeoBasicCluster(Basic, LocalDataCluster):
    """Candeo Basic Cluster."""

    class AttributeDefs(Basic.AttributeDefs):
        """Attribute Definitions."""

        actions_detection = ZCLAttributeDef(
            id=0x8803,
            type=CandeoActionsDetection,
            zcl_type=DataTypeId.uint8,
            access="rw",
        )
        actions_window = ZCLAttributeDef(
            id=0x8804,
            type=CandeoActionsWindow,
            zcl_type=DataTypeId.uint16,
            access="rw",
        )
    
    _CONSTANT_ATTRIBUTES = { }
    
    _VALID_ATTRIBUTES = { AttributeDefs.actions_detection.id, AttributeDefs.actions_window.id }    
    
    attr_config = { AttributeDefs.actions_detection.id: CandeoActionsDetection.single, AttributeDefs.actions_window.id: CandeoActionsWindow.wait_500_ms }

    def __init__(self, *args, **kwargs):
        """__init___."""
        self._configured = False
        super().__init__(*args, **kwargs)

    async def apply_custom_configuration(self, *args, **kwargs):
        """Apply custom configuration to setup preferences."""
        self.debug("CandeoBasicCluster: apply_custom_configuration called")
        self.debug("CandeoBasicCluster: self._configured - [%s]", self._configured)
        if not self._configured:
            await self.write_attributes(self.attr_config)
            self._configured = True


class CandeoOnOffCluster(OnOff, LocalDataCluster):
    """Candeo OnOff Cluster."""

    class AttributeDefs(OnOff.AttributeDefs):
        """Attribute Definitions."""

        action = ZCLAttributeDef(
            id=0x0000, 
            type=t.Bool, 
            access="rps", 
            mandatory=True
        )      

    def __init__(self, *args, **kwargs):
        """__init___."""
        self._loop = asyncio.get_running_loop()
        self._timer_handle = None
        self._click_count = 0
        self._actions_window = None
        self._actions_detection = None
        super().__init__(*args, **kwargs) 

    def _update_attribute(self, attrid, value):
        """Override _update_attribute."""
        self.debug("CandeoOnOffCluster: _update_attribute called")
        self.debug("CandeoOnOffCluster: attrid - [%s] value - [%s]", attrid, value)
        self.debug("CandeoOnOffCluster: endpoint_id - [%s]",  self.endpoint.endpoint_id)   
        super()._update_attribute(attrid, value)
        if attrid == self.AttributeDefs.action.id:
            self.debug("CandeoOnOffCluster: got action attribute")
            self._click_count += 1
            self.debug("CandeoOnOffCluster: _click_count - [%s]", self._click_count)
            self.get_preferences()
            self.debug("CandeoOnOffCluster: self._actions_window - [%s]", self._actions_window)
            self.debug("CandeoOnOffCluster: self._actions_detection - [%s]", self._actions_detection)
            if self._actions_detection > 1:
                self.debug("CandeoOnOffCluster: actions detection set to multi-press detection!")
                if self._timer_handle:
                    self.debug("CandeoOnOffCluster: cancel existing timer")
                    self._timer_handle.cancel()
                self._timer_handle = self._loop.call_later(self._actions_window / 1000, self.action_detection)
            else:
                self.debug("CandeoOnOffCluster: actions detection limited to single by setting or default, skipping multi-press detection!")
                self.action_detection()

    def action_detection(self):
        """Action detection."""
        self.debug("CandeoOnOffCluster: action_detection called")
        endpoint_id = self.endpoint.endpoint_id
        self.debug("CandeoOnOffCluster: endpoint_id - [%s]", endpoint_id)        
        self.debug("CandeoOnOffCluster: _click_count - [%s]", self._click_count)
        self.get_preferences()
        self.debug("CandeoOnOffCluster: _actions_window - [%s]", self._actions_window)
        self.debug("CandeoOnOffCluster: _actions_detection - [%s]", self._actions_detection)
        self._timer_handle = None
        click_count = self._click_count
        if click_count <= self._actions_detection:
            button_action = CandeoButtonActions._value2member_map_.get(click_count)
            if button_action:            
                self.listener_event(
                    ZHA_SEND_EVENT,
                    button_action.name, {}
                )
            else:
                self.debug("CandeoOnOffCluster: got unexpected click count!")
        else:
            self.debug("CandeoOnOffCluster: setting or default disables events for this combination!")
        self._click_count = 0

    def get_preferences(self):
        """Get preferences."""
        self.debug("CandeoOnOffCluster: get_preferences called")
        cluster = self.endpoint.in_clusters.get(CandeoBasicCluster.cluster_id)
        if cluster is None:
            self.debug("CandeoOnOffCluster: basic cluster not available yet")
            return
        self._actions_window = cluster._attr_cache.get(CandeoBasicCluster.AttributeDefs.actions_window.id) or CandeoActionsWindow.wait_500_ms
        self.debug("CandeoOnOffCluster: self._actions_window - [%s]", self._actions_window) 
        self._actions_detection = cluster._attr_cache.get(CandeoBasicCluster.AttributeDefs.actions_detection.id) or CandeoActionsDetection.single
        self.debug("CandeoOnOffCluster: self._actions_detection - [%s]", self._actions_detection)


quirk_base = (
    QuirkBuilder()
    .replace_cluster_occurrences(CandeoOnOffCluster)
    .replace_cluster_occurrences(CandeoBasicCluster)
)

(
    quirk_setup(quirk_base, 10)
    .applies_to(CANDEO, "C-RFZB-HUB")
    .add_to_registry()
)
