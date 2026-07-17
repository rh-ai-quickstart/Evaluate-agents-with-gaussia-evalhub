# Gaussia EvalHub Quickstart UI

Streamlit dashboard for browsing scenario fixtures, submitting Gaussia EvalHub evaluation runs, and inspecting run history on OpenShift.

## What it does

The UI wraps the same Makefile targets used in the CLI quickstart:

| Page | Purpose |
| --- | --- |
| **Fixtures** | Inspect the included agent conversation scenarios (first-line support, retail, root-cause analysis). |
| **Run Evaluation** | Submit `humanity`, full-suite, external EvalHub, or local `uv` runs against the selected fixture. |
| **Run History & Logs** | Check platform status and follow job logs for a run. |

Sidebar controls set the OpenShift namespace, Helm release name, and selected fixture used by those flows.

## Layout

```text
apps/ui/
├── app.py                 # Entrypoint (`streamlit run app.py`)
├── Containerfile.ui       # Container image for the dashboard
├── requirements.txt
├── .streamlit/            # Streamlit theme and server config
└── assets/                # Logos and static assets
```

## Run locally

From the repository root (with cluster/`oc` access and a configured `.env` as described in the main README):

```bash
pip install -r apps/ui/requirements.txt
streamlit run apps/ui/app.py
```

Or build and run the container image with podman (build context is the repository root):

```bash
podman build -f apps/ui/Containerfile.ui -t gaussia-evalhub-ui .
podman run --rm -p 8501:8501 gaussia-evalhub-ui
```

The dashboard can also be deployed with the combined Helm chart at `deploy/helm` (`ui.enabled=true`).
