from datetime import datetime, timezone
from typing import Dict, List, Set

from flask import request
from pydantic import BaseModel, Field

import os
import sys
import docker

from lp_ap_tools.lp_ap_tools import LP_artefact, add_lp_params, print_attributes

from globus_action_provider_tools import (
    ActionProviderDescription,
    ActionRequest,
    ActionStatus,
    ActionStatusValue,
    AuthState,
)
from globus_action_provider_tools.authorization import (
    authorize_action_access_or_404,
    authorize_action_management_or_404,
)
from globus_action_provider_tools.flask import ActionProviderBlueprint
from globus_action_provider_tools.flask.exceptions import ActionConflict, ActionNotFound
from globus_action_provider_tools.flask.types import (
    ActionCallbackReturn,
    ActionLogReturn,
)

from backend import action_database, request_database

# Globals for directory locations 
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_DIR = os.path.join(CURRENT_DIR, 'input') # AP inputs for method execution
OUTPUT_DIR = os.path.join(CURRENT_DIR, 'output') # Generated outputs
METHOD_DIR = os.path.join(CURRENT_DIR, 'method_resources') # Resources for method execution (e.g. Model, code, etc.)
CRATES_DIR = os.path.join(CURRENT_DIR, 'crates') # ROcrate location for each action
directory_structure = {"input": INPUT_DIR, "output": OUTPUT_DIR, "method": METHOD_DIR, "crates": CRATES_DIR}

class ActionProviderInput(BaseModel):
    # Defines the required input for the Action Provider (E.G. directories to process)
    example: str = Field(
        ..., title="Some required input", description="A useful description"
    )
    
    # Defines the returned dialog when querying the Action Provider
    class Config:
        schema_extra = {
            "example": {
                "example": "an example of the variable"
                }
            }

# Using lp_ap_tools, we can add LP fields to the ActionProviderInput 
# post-hoc, providing flexibility in the chosen fields.
ActionProviderInput = add_lp_params(ActionProviderInput)

# Configure Action Provider identity
description = ActionProviderDescription(
    globus_auth_scope="https://auth.globus.org/scopes/b92716c9-3ac2-4315-8f48-c33148efed20/action_provider_operations",
    title="",
    admin_contact="",
    synchronous=True,
    input_schema=ActionProviderInput,
    api_version="1.0",
    subtitle="",
    description="An example ActionProvider that uses a container to copy a file from input to output",
    keywords=[""],
    visible_to=["public"],
    runnable_by=["all_authenticated_users"],
    administered_by=[""],
)

# Configure name, url and assign description
aptb = ActionProviderBlueprint(
    name="example",
    import_name=__name__,
    url_prefix="/example",
    provider_description=description
)

# ---------------------------------------------------------------------
# --------------------- Action Provider endpoints ---------------------
# ---------------------------------------------------------------------

@aptb.action_enumerate
def action_enumeration(auth: AuthState, params: Dict[str, Set]) -> List[ActionStatus]:
    """
    This is an optional endpoint, useful for allowing requestors to enumerate
    actions filtered by ActionStatus and role.

    The params argument will always be a dict containing the incoming request's
    validated query arguments. There will be two keys, 'statuses' and 'roles',
    where each maps to a set containing the filter values for the key. A typical
    params object will look like:

        {
            "statuses": {<ActionStatusValue.ACTIVE: 3>},
            "roles": {"creator_id"}
        }

    Notice that the value for the "statuses" key is an Enum value.
    """
    statuses = params["statuses"]
    roles = params["roles"]
    matches = []

    for _, action in action_database.items():
        if action.status in statuses:
            # Create a set of identities that are allowed to access this action,
            # based on the roles being queried for
            allowed_set = set()
            for role in roles:
                identities = getattr(action, role)
                if isinstance(identities, str):
                    allowed_set.add(identities)
                else:
                    allowed_set.update(identities)

            # Determine if this request's auth allows access based on the
            # allowed_set
            authorized = auth.check_authorization(allowed_set)
            if authorized:
                matches.append(action)

    return matches

@aptb.action_run
def my_action_run(action_request: ActionRequest, auth: AuthState) -> ActionCallbackReturn:
    """
    Implement custom business logic related to instantiating an Action here.
    Once launched, collect details on the Action and create an ActionStatus
    which records information on the instantiated Action and gets stored.
    """
    
    # Regestration of action
    print('Action running', file=sys.stderr)
    print(f'Action request ID: {action_request.request_id}', file=sys.stderr)

    # Regester action request to parse out continuing requests
    caller_id = auth.effective_identity
    full_request_id = f"{caller_id}:{action_request.request_id}"
    prev_request = request_database.get(full_request_id)

    if prev_request is not None:
        """
        NOTE: This is needed because the Globus client sends multiple
        post requests to the server when starting an action. This stops 
        further requests once a unique action is logged, and returns 
        the status of the currently logged request.
        """
        if prev_request[0] == request:
            return my_action_status(prev_request[1], auth)
        else:
            raise ActionConflict(
                f"Request with id {full_request_id} already present with different parameters"
            )
        
    action_status = ActionStatus(
        status=ActionStatusValue.ACTIVE,
        creator_id=str(auth.effective_identity),
        label=action_request.label or None,
        monitor_by=action_request.monitor_by or auth.identities,
        manage_by=action_request.manage_by or auth.identities,
        start_time=datetime.now(timezone.utc).isoformat(),
        completion_time=None,
        release_after=action_request.release_after or "P30D",
        display_status=ActionStatusValue.ACTIVE,
        details={},
    )
    # Update action_database with action object
    action_database[action_status.action_id] = action_status
    # update request_database with unique request ID
    request_database[full_request_id] = (request, action_status.action_id)

    print(request_database[full_request_id])

    # Example logic for running an action
    run_computation(ap_description=description, 
                    ap_request=action_request, 
                    ap_status=action_status,
                    ap_auth=auth,
                    ap_apbt=aptb,
                    raw_request=request_database[full_request_id]) 

    return action_status

# LP artefact decorator for ROcrate management
# TODO: integrate management_ep with AP params, as a constant
@LP_artefact(dir_struct=directory_structure)
def run_computation(ap_description: ActionProviderDescription, 
                    ap_request: ActionRequest, 
                    ap_status: ActionStatus,
                    ap_auth: AuthState,
                    ap_apbt: ActionProviderBlueprint,
                    raw_request: request):

    # ----------------------------------------------
    # ----------- docker containersation -----------
    # ----------------------------------------------

    client = docker.from_env()
    # bind constant input/output directories to import and export data 
    # between the external context and the container
    volumes = {
        INPUT_DIR: {'bind': '/computation/input', 'mode': 'rw'},
        OUTPUT_DIR: {'bind': '/computation/output', 'mode': 'rw'}
    }

    try: 
        print("Executing container")
        # Image is built and named in app.py
        container = client.containers.run(
            image='computation_image:latest',
            volumes=volumes,
            detach=True
        )
        # wait for the container to finish
        container.wait()

    except Exception as e:
        print(e)
    
    finally:
        # If the conatiner is still running, stop it
        if container.status == 'running':
            container.stop()
        # Remove the container
        container.remove()

    


@aptb.action_status
def my_action_status(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Query for the action_id in some storage backend to return the up-to-date
    ActionStatus. It's possible that some ActionProviders will require querying
    an external system to get up to date information on an Action's status.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")
    authorize_action_access_or_404(action_status, auth)
    return action_status


@aptb.action_cancel
def my_action_cancel(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Only Actions that are not in a completed state may be cancelled.
    Cancellations do not necessarily require that an Action's execution be
    stopped. Once cancelled, the ActionStatus object should be updated and
    stored.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")

    authorize_action_management_or_404(action_status, auth)
    if action_status.is_complete():
        raise ActionConflict("Cannot cancel complete action")

    action_status.status = ActionStatusValue.FAILED
    action_status.display_status = f"Cancelled by {auth.effective_identity}"
    action_database[action_id] = action_status
    return action_status


@aptb.action_release
def my_action_release(action_id: str, auth: AuthState) -> ActionCallbackReturn:
    """
    Only Actions that are in a completed state may be released. The release
    operation removes the ActionStatus object from the data store. The final, up
    to date ActionStatus is returned after a successful release.
    """
    action_status = action_database.get(action_id)
    if action_status is None:
        raise ActionNotFound(f"No action with {action_id}")

    authorize_action_management_or_404(action_status, auth)
    if not action_status.is_complete():
        raise ActionConflict("Cannot release incomplete Action")

    action_status.display_status = f"Released by {auth.effective_identity}"
    # TODO currently dont understand the release mechanic and this might break
    request_database.pop(action_id)
    action_database.pop(action_id)
    return action_status


@aptb.action_log
def my_action_log(action_id: str, auth: AuthState) -> ActionLogReturn:
    """
    Action Providers can optionally support a logging endpoint to return
    detailed information on an Action's execution history. Pagination and
    filters are supported as query parameters and can be used to control what
    details are returned to the requestor.
    """
    pagination = request.args.get("pagination")
    filters = request.args.get("filters")
    return ActionLogReturn(
        code=200,
        description=f"This is an example of a detailed log entry for {action_id}",
        **{
            "time": "TODAY",
            "details": {
                "action_id": "Transfer",
                "filters": filters,
                "pagination": pagination,
            },
        },
    )


# Testing
# if __name__ == "__main__":
#     run_computation()
