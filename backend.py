from typing import Dict, Tuple

from globus_action_provider_tools import ActionStatus
from globus_action_provider_tools.data_types import ActionRequest
from globus_action_provider_tools.storage import AbstractActionRepository

action_database: Dict[str, ActionStatus] = {}
request_database: Dict[str, Tuple[ActionRequest, str]] = {}

class ActionRepo(AbstractActionRepository):
    repo: dict = {}

    def get(self, action_id: str):
        return self.repo.get(action_id, None)

    def store(self, action: ActionStatus):
        self.repo[action.action_id] = action

    def remove(self, action: ActionStatus):
        del self.repo[action.action_id]