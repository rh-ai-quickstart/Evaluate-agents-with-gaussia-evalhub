# Gaussia EvalHub Quickstart UI

Streamlit dashboard for browsing scenario fixtures and submitting Gaussia EvalHub
evaluation runs via the EvalHub API.

## What it does

| Page | Purpose |
| --- | --- |
| **Fixtures** | Inspect the included agent conversation scenarios (first-line support, retail, root-cause analysis). |
| **Run Evaluation** | Submit `humanity` or full-suite benchmarks against the selected fixture through the EvalHub SDK. |
| **Jobs** | List and inspect EvalHub jobs by id. |

The UI calls EvalHub directly (same path as `apps/evalhub_job_submission/submit_evalhub_job.py`).
It does **not** create OpenShift submit Jobs — those remain Make-only (`make run-humanity`, `make run-all`, `make install-external`).

## Layout

```text
apps/ui/
├── app.py                 # Entrypoint (`streamlit run app.py`)
├── config.py              # Paths and shared UI configuration
├── Containerfile.ui       # Container image for the dashboard
├── requirements.txt
├── clients/               # EvalHub API client
├── components/            # Sidebar, styles, shared UI helpers
├── views/                 # Fixtures, Run Evaluation, Jobs views
├── services/              # Fixture discovery and evaluation orchestration
├── .streamlit/            # Streamlit theme and server config
└── assets/                # Logos and static assets
```

## Run locally

From the repository root (with `EVALHUB_*` configured in `.env` as described in the main README):

```bash
pip install -r apps/ui/requirements.txt
streamlit run apps/ui/app.py
```

Or build and run the container image with podman (build context is the repository root):

```bash
podman build -f apps/ui/Containerfile.ui -t gaussia-evalhub-ui .
podman run --rm -p 8501:8501 --env-file .env gaussia-evalhub-ui
```

The dashboard can also be deployed with the combined Helm chart at `deploy/helm` (`ui.enabled=true`).
The UI ConfigMap injects non-secret `EVALHUB_*` / model settings for in-cluster EvalHub.
`GAUSSIA_JUDGE_API_KEY` and `GAUSSIA_GUARDIAN_API_KEY` come from the chart-managed provider Secret (or `platform.provider.existingSecret`) via `envFrom.secretRef`.
