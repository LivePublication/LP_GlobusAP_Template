# LP_GlobusAP_Template 

## What this repository does

Provides a Flask-based template for a Globus Action Provider (AP) that integrates Distriubted Step Crate Generation. Each Action invocation is structured to execute a step (via Docker in this template) and emit a per-step RO-Crate provenance fragment intended for Distributed Step Crate (DSC) aggregation.

## Repository structure
- `app.py`: Flask entrypoint; registers the Action Provider blueprint and checks/creates the Docker image.
- `blueprint.py`: Action Provider definition, endpoints, and step execution wrapper (`LP_artefact`).
- `backend.py`: in-memory action storage.
- `config.py`: Globus Auth credentials (placeholder values).
- `requirements.txt`: Python dependencies.
- `method_resources/`: template location for Docker build context (currently empty).
- `input/`, `output/`: example data directories used by the template run.
- `crates/`: target location for generated RO-Crate fragments.
- `scope_definitions/`: example scope configuration JSON files.

## Inputs
- `input_data` (string, required): path or argument passed to the container (typically under `input/`).
- `management_ep_id` (string, required): Globus endpoint UUID used for crate transfer (added via `lp_ap_tools.add_lp_params`).

## Outputs
- Per-action RO-Crate fragments written under `crates/` (template behavior).
- Any workflow output files written under `output/`.
- Optional Globus Transfer submissions to the management endpoint (template behavior).

## Quickstart
1) Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) Configure Globus credentials and provider metadata:
- Edit `config.py` with your Globus Auth `CLIENT_ID` and `CLIENT_SECRET`.
- Update the `ActionProviderDescription` fields in `blueprint.py` (title, scope, api_version, etc.).

3) Start the service:

```bash
python app.py
# Listens on http://0.0.0.0:8080
```

4) Run an action (example):

```bash
curl -X POST \
  http://localhost:8080/actions \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
        "input_data": "input/test.txt",
        "management_ep_id": "<YOUR-MANAGEMENT-ENDPOINT-UUID>"
      }'
```

## How to cite
- GitHub: https://github.com/LivePublication/LP_GlobusAP_Template
- Zenodo DOI: (minted after release)

## License
Apache-2.0. See `LICENSE`.
