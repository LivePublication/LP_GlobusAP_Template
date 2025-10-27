## Project Overview

This repository is a Flask-based Globus Action Provider (AP) template extended to generate per-step distributed step crates. Each Action invocation runs a remote/distributed step (via Docker in this template) and generates a machine-readable provenance fragment as an RO-Crate. The crate is written locally under `crates/` and optionally transferred to a designated management Globus endpoint for aggregation.

## API / Provenance Endpoint(s)

Endpoints are provided by `globus_action_provider_tools` via the `ActionProviderBlueprint`. Paths shown below are enabled by this template (url_prefix empty):

- GET `/` — Introspection: returns the Action Provider description (requires authorization per `visible_to`).
- GET `/actions` — Enumeration: list Actions filtered by status/roles that the caller can access.
- POST `/actions` (alias: POST `/run`) — Run a new Action. Body must satisfy the input schema (see below).
- GET `/actions/<action_id>` — Status for the given Action.
- POST `/actions/<action_id>/cancel` — Cancel an in-progress Action.
- DELETE `/actions/<action_id>` — Release a completed Action (removes from repo; see notes).
- GET `/actions/<action_id>/log` — Optional log info for the Action.

Input schema for POST `/actions` (this template):

- `input_data` (string, required): passed to the container as a command argument; typically a path under `input/`.
- `management_ep_id` (string, required): Globus endpoint UUID to which the crate will be transferred. Added by `lp_ap_tools.add_lp_params`.

Auth: All endpoints use bearer tokens validated by `TokenChecker`. The accepted scopes are configured from the Action Provider description (and any additional scopes). You must send an `Authorization: Bearer <access_token>` header.

## Running the Service

Prerequisites:

- Python 3.11+
- Docker daemon available locally (for the computation step)
- Globus Connect Personal (GCP) running on the host for crate transfer
- A Globus Auth application with client id/secret configured

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure credentials:

- Edit `config.py` to set `CLIENT_ID` and `CLIENT_SECRET` for your Globus Auth application.
- Update the `ActionProviderDescription` in `blueprint.py` with your real values (title, scope, api_version, etc.).

Start the service:

```bash
python app.py
# The service listens on http://0.0.0.0:8080
```

Docker image build note:

- On startup, `app.py` checks for `computation_image:latest` and, if missing, attempts to build from `method_resources/computation_docker`.

Globus transfer note:

- The crate transfer uses `LocalGlobusConnectPersonal()` and dependent tokens. Ensure GCP is installed and running, and that the bearer token used to call the AP has rights to request dependent tokens for Transfer.

## Example Usage

(A) Start the service locally

```bash
python app.py
```

(B) Run a provenance-enabled action

```bash
curl -X POST \
	http://localhost:8080/actions \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{
				"input_data": "input/test.txt",
				"management_ep_id": "<YOUR-MANAGEMENT-ENDPOINT-UUID>"
			}'

# Expected response (example):
# {
#   "action_id": "...",
#   "status": "ACTIVE" | "SUCCEEDED" | "FAILED",
#   "creator_id": "urn:globus:auth:identity:<id>",
#   ...
# }
# The step crate is written to crates/crate_<action_id> and a Globus Transfer is submitted to your management endpoint.
```
