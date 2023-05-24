from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod

from gladier import GladierBaseTool
from typing_extensions import TypeAlias

JSONObject: TypeAlias = t.Dict[str, "JSONValue"]
JSONList: TypeAlias = t.List["JSONValue"]
JSONValue: TypeAlias = t.Union[JSONObject, JSONList, str, int, float, bool, None]


def get_action_param_name(param_name: str, param_val: str | int | bool | dict) -> str:
    if isinstance(param_val, str) and param_val.startswith("$."):
        return param_name + ".$"
    else:
        return param_name


class GladierExperimentalBaseTool(GladierBaseTool, ABC):
    def __init__(
        self, state_name: str | None = None, state_comment: str | None = None, **kwargs
    ):
        if state_name is None:
            state_name = str(type(self))
        self.state_name = state_name
        if state_comment is None:
            state_comment = f"State named {state_name}"
        self.state_comment = state_comment
        super().__init__(**kwargs)

    @abstractmethod
    def set_flow_definition(self) -> JSONObject:
        if self.flow_definition is not None:
            return self.flow_definition
        self.flow_definition: JSONObject = {
            "Comment": self.state_comment,
            "StartAt": self.state_name,
            "States": {
                self.state_name: {
                    "Comment": self.state_comment,
                }
            },
        }
        return self.flow_definition

    def get_dict_for_flow_state(self) -> JSONObject:
        flow_def = GladierExperimentalBaseTool.set_flow_definition(self)
        flow_states: JSONObject = flow_def.get("States", {})
        return flow_states[self.state_name]

    def get_flow_definition(self) -> JSONObject:
        return self.set_flow_definition()

    @property
    def required_input(self) -> list[str]:
        """
        Attempt to scrape required input from the properties of the self
        object. If a value starts with the JSONPath prefix '$.input.' we assume
        it is intended to be one of the required inputs to this state.
        """
        return_list: list[str] = []
        required_input_prefix = "$.input."
        for prop_val in vars(self).values():
            if isinstance(prop_val, str) and prop_val.startswith(required_input_prefix):
                return_list.append(prop_val[len(required_input_prefix) :])
        return return_list


class GladierExperimentalBaseActionTool(GladierExperimentalBaseTool, ABC):
    def __init__(
        self,
        action_url: str,
        action_scope: str | None = None,
        wait_time: int = 600,
        result_path: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.action_url = action_url
        self.action_scope = action_scope
        self.wait_time = wait_time
        if result_path is None:
            result_path = f"$.{self.state_name}Result"
        if not result_path.startswith("$."):
            result_path = "$." + result_path
        self.result_path = result_path
        self.parameters: JSONObject | None = None
        self.input_path: str | None = None

    def set_flow_definition(self) -> JSONObject:
        flow_state = self.get_dict_for_flow_state()
        flow_state.update(
            {
                "Type": "Action",
                "ActionUrl": self.action_url,
                "ResultPath": self.result_path,
                "WaitTime": self.wait_time,
                "End": True,
            }
        )
        if self.action_scope is not None:
            flow_state["ActionScope"] = self.action_scope
        if self.required_input is not None:
            flow_state["InputPath"] = self.input_path
        if self.parameters is not None:
            flow_state["Parameters"] = self.parameters
        return self.flow_definition
