# LP_GlobusAP_Template (Thesis Artifact)

## What this repository does
Provides a Flask-based template for a Globus Action Provider (AP) that integrates LivePublication provenance export patterns. Each Action invocation is structured to execute a step (via Docker in this template) and emit a per-step RO-Crate provenance fragment intended for Distributed Step Crate (DSC) aggregation.

## How it fits into the thesis
This repository supports Chapter 5 (Provenance for Distributed Workflow Management Systems) by providing a Globus-side scaffold for step-level provenance capture and packaging. It aligns with Distributed Step Crate (DSC) generation patterns in Globus-based distributed execution environments and should be treated as a template/starting point rather than a complete, deployed service.

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

TODO:
- Provide a Dockerfile or image definition under `method_resources/computation_docker` so the template can build `computation_image:latest`.
- Document the expected RO-Crate output structure in `crates/` once DSC conventions are finalized.

## Reproducibility notes
- Requires a running Docker daemon for the computation step.
- Requires Globus Auth credentials and Globus Connect Personal for Transfer-based crate export.
- The Globus Action Provider behavior is implemented using `globus_action_provider_tools` and `lp-ap-tools`.
- This repository is a template; production deployment requires filling in Action Provider metadata and scopes.

## How to cite
- GitHub: https://github.com/LivePublication/LP_GlobusAP_Template
- Zenodo DOI: (minted after release)

## License
Apache-2.0. See `LICENSE`.
