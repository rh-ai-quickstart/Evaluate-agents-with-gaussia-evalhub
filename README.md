# Evaluate agents with Gaussia and EvalHub

Use this AI quickstart to measure agent conversations with Gaussia benchmarks, EvalHub jobs, and MLflow metrics on Red Hat® OpenShift® AI.

## Table of contents

- [Detailed description](#detailed-description)
  - [See it in action](#see-it-in-action)
  - [Architecture diagrams](#architecture-diagrams)
- [Requirements](#requirements)
  - [Minimum hardware requirements](#minimum-hardware-requirements)
  - [Minimum software requirements](#minimum-software-requirements)
  - [Required user permissions](#required-user-permissions)
- [Deploy](#deploy)
  - [Prerequisites](#prerequisites)
  - [Run the local smoke test](#run-the-local-smoke-test)
  - [Submit a live EvalHub job](#submit-a-live-evalhub-job)
  - [Deploy the OpenShift smoke job](#deploy-the-openshift-smoke-job)
  - [Deploy the OpenShift EvalHub submit job](#deploy-the-openshift-evalhub-submit-job)
  - [Validate results](#validate-results)
  - [Delete](#delete)
- [References](#references)
- [Technical details](#technical-details)
  - [Payload contract](#payload-contract)
  - [Benchmark selection](#benchmark-selection)
  - [Model and run metadata](#model-and-run-metadata)
  - [Repository structure](#repository-structure)
- [Tags](#tags)

## Detailed description

This AI quickstart shows how platform, product, and model teams can evaluate agent conversations with repeatable benchmarks. It uses Gaussia as the evaluation provider, EvalHub as the job orchestration layer, and MLflow as the metrics and run history backend.

Agentic systems are difficult to measure with only manual review. A support agent may sound helpful while losing context, giving inconsistent answers, or drifting into low-quality response patterns over a longer session. This quickstart turns an agent transcript into a structured EvalHub job and runs Gaussia benchmarks against that transcript so teams can compare releases, inspect metrics, and decide what to improve next.

The included fixtures use a first-line support scenario. The same pattern applies to other agent workflows, including IT service desk agents, incident response assistants, customer support agents, and internal operations agents. The primary flow is intentionally agnostic to any source runtime: any system that can produce `dataset + metadata` can create the same EvalHub job.

This quickstart demonstrates:

- Local validation of the Gaussia EvalHub adapter without a cluster.
- Submission of a real EvalHub job using the preferred `dataset + metadata` payload.
- OpenShift execution through a minimal Helm chart.
- MLflow-ready metadata for dataset, source, and evaluated model tracking.
- An optional integration path for Alquimia Runtime as an event source.

### See it in action

The default smoke test runs the `humanity` benchmark against a deterministic agent transcript and prints EvalHub-compatible results:

```json
{
  "benchmark_id": "humanity",
  "model_name": "support-agent-demo-v1",
  "num_examples_evaluated": 5,
  "evaluation_metadata": {
    "payload_source": "dataset",
    "primary_metric_name": "humanity_assistant_emotional_entropy"
  }
}
```

When connected to EvalHub and MLflow, the same dataset creates one EvalHub job, benchmark-specific EvalHub child jobs, and one MLflow run per benchmark.

### Architecture diagrams

![Architecture diagram showing an agent transcript sent to EvalHub, evaluated by the Gaussia provider, and logged to MLflow](docs/images/gaussia-evalhub-architecture.svg)

**Flow summary:**

1. A source system exports an agent transcript as a Gaussia-compatible dataset.
2. The quickstart submits an EvalHub job with one benchmark entry per selected Gaussia metric family.
3. EvalHub starts the Gaussia provider adapter with `python -m gaussia.integrations.evalhub.adapter`.
4. The provider evaluates the dataset, reports results to EvalHub, and logs metrics, datasets, sources, and model metadata to MLflow.

## Requirements

### Minimum hardware requirements

**Local smoke test:**

- CPU: 2 vCPU.
- Memory: 4 GiB.
- Storage: 2 GiB for Python dependencies and temporary artifacts.
- GPU: not required for the default `humanity` benchmark.

**OpenShift smoke or submit job:**

- CPU: 2 vCPU request, 4 vCPU limit.
- Memory: 4 GiB request, 8 GiB limit.
- Storage: 5 GiB ephemeral storage.
- GPU: not required unless your selected judge, guardian, or toxicity configuration uses an on-cluster model that requires GPU acceleration.

### Minimum software requirements

- Python 3.12+.
- [uv](https://docs.astral.sh/uv/) for local quickstart commands.
- Helm 3.x.
- OpenShift CLI `oc`.
- Red Hat OpenShift 4.18+.
- Red Hat OpenShift AI 2.16+ when using OpenShift AI hosted MLflow or model-serving endpoints.
- A public release of `gaussia[evalhub]`.
- EvalHub endpoint and token for live job submission.
- MLflow tracking endpoint for persisted benchmark runs.

### Required user permissions

- Local smoke test: no cluster permissions.
- EvalHub submit job: EvalHub token with permission to create jobs in the configured tenant.
- OpenShift smoke job: namespace-level permission to create ConfigMaps, Secrets, Jobs, Pods, and ServiceAccounts.
- Provider registration in a shared EvalHub installation may require platform administrator access, depending on how EvalHub is managed in your environment.

## Deploy

### Prerequisites

Clone the repository:

```bash
git clone https://github.com/rh-ai-quickstart/Evaluate-agents-with-gaussian-evalhub.git
cd Evaluate-agents-with-gaussian-evalhub
```

### Run the local smoke test

Run the adapter locally with the long fixture and the `humanity` benchmark. This path does not require EvalHub, MLflow, OpenShift, judge credentials, or guardian credentials.

```bash
uv run \
  --with "gaussia[evalhub]" \
  python quickstart/local_provider_smoke.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks humanity
```

Expected output includes:

```json
{
  "benchmark_id": "humanity",
  "model_name": "support-agent-demo-v1",
  "num_examples_evaluated": 5
}
```

To use the benchmark selector, run:

```bash
uv run \
  --with "gaussia[evalhub]" \
  python quickstart/local_provider_smoke.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks auto
```

The long fixture selects `humanity`, `context`, `conversational`, `bias`, and `toxicity`. Configure the required `GAUSSIA_*` judge, guardian, and toxicity settings before running model-backed benchmarks.

### Submit a live EvalHub job

Configure EvalHub access:

```bash
export EVALHUB_BASE_URL="https://evalhub.example.com"
export EVALHUB_AUTH_TOKEN="<token>"
export EVALHUB_TENANT="default"
export EVALHUB_INSECURE="false"
export EVALHUB_EXPERIMENT_NAME="gaussia-agent-evaluation"
export GAUSSIA_EVALUATED_MODEL_NAME="support-agent-demo-v1"
export GAUSSIA_EVALUATED_MODEL_URL="https://example.invalid/models/support-agent-demo-v1"
```

Submit the short fixture. It creates one EvalHub job with three benchmarks:

```bash
uv run \
  --with "gaussia[evalhub]" \
  --with "eval-hub-sdk[client]==0.1.5" \
  python quickstart/submit_evalhub_job.py \
    --fixture quickstart/fixtures/agent_transcript_short.json \
    --benchmarks auto
```

Submit the long fixture. It creates one EvalHub job with five benchmarks:

```bash
uv run \
  --with "gaussia[evalhub]" \
  --with "eval-hub-sdk[client]==0.1.5" \
  python quickstart/submit_evalhub_job.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks auto \
    --unique-run
```

Expected output includes:

```json
{
  "status": "submitted",
  "job_id": "...",
  "benchmark_ids": [
    "humanity",
    "context",
    "conversational",
    "bias",
    "toxicity"
  ]
}
```

### Deploy the OpenShift smoke job

Create a namespace and install the Helm chart in smoke mode:

```bash
export NAMESPACE="gaussia-evalhub-quickstart"

oc new-project "${NAMESPACE}"

helm install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --set mode=smoke \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=humanity
```

Watch the job:

```bash
oc logs job/gaussia-evalhub-smoke -n "${NAMESPACE}" -f
```

### Deploy the OpenShift EvalHub submit job

Install in submit mode with EvalHub credentials:

```bash
helm upgrade --install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --set mode=submit \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=auto \
  --set evalhub.baseUrl="${EVALHUB_BASE_URL}" \
  --set evalhub.authToken="${EVALHUB_AUTH_TOKEN}" \
  --set evalhub.tenant="${EVALHUB_TENANT}" \
  --set evalhub.insecure="${EVALHUB_INSECURE}" \
  --set evalhub.experimentName="${EVALHUB_EXPERIMENT_NAME}" \
  --set evaluatedModel.name="${GAUSSIA_EVALUATED_MODEL_NAME}" \
  --set evaluatedModel.url="${GAUSSIA_EVALUATED_MODEL_URL}"
```

For production-style usage, create the secret separately and set `evalhub.existingSecret` instead of passing `evalhub.authToken` on the command line.

To rerun the same mode with different values, uninstall the release first. Kubernetes Jobs are immutable after creation.

### Validate results

Use these checks to confirm the quickstart completed:

```bash
oc get jobs,pods -n "${NAMESPACE}"
oc logs job/gaussia-evalhub-submit -n "${NAMESPACE}"
```

In EvalHub, confirm that the long fixture created one top-level job with five benchmark jobs.

In MLflow, confirm that each benchmark run includes:

- dataset name beginning with `gaussia-`.
- source name `gaussia.integrations.evalhub.adapter`.
- evaluated model name from `GAUSSIA_EVALUATED_MODEL_NAME`.
- tags for `assistant_id`, `session_id`, `stream_id`, and `control_id`.

### Delete

Remove the Helm release:

```bash
helm uninstall gaussia-evalhub --namespace "${NAMESPACE}"
```

Delete the namespace if it was created only for this quickstart:

```bash
oc delete project "${NAMESPACE}"
```

## References

- [Gaussia documentation](https://github.com/gaussia-labs/pygaussia)
- [EvalHub provider adapter entrypoint](https://github.com/gaussia-labs/pygaussia)
- [Red Hat AI quickstart template](https://github.com/rh-ai-quickstart/ai-quickstart-template)
- [Alquimia Runtime integration notes](docs/alquimia-runtime-integration.md)

## Technical details

### Payload contract

The public quickstart uses the preferred EvalHub provider contract:

```json
{
  "parameters": {
    "dataset": {
      "session_id": "support-agent-long-session",
      "assistant_id": "support-resolution-agent",
      "language": "english",
      "context": "The agent supports first-line incident triage.",
      "conversation": []
    },
    "metadata": {
      "stream_id": "support-agent-long-stream",
      "control_id": "support-agent-long-control",
      "source": "gaussia.quickstart.agent-transcript.v1"
    }
  }
}
```

The Gaussia EvalHub adapter still accepts the legacy `context_persistance` payload for systems that already emit it. New integrations should use `dataset + metadata`.

### Benchmark selection

The quickstart selector always includes:

- `humanity`
- `context`
- `conversational`

When the dataset has five or more interactions, it also includes:

- `bias`
- `toxicity`

Use `--benchmarks humanity` for a no-credential smoke test.

### Model and run metadata

The evaluated model is the agent or model version represented by the transcript, not the judge model used by a benchmark. Set it with:

```bash
export GAUSSIA_EVALUATED_MODEL_NAME="support-agent-demo-v1"
export GAUSSIA_EVALUATED_MODEL_URL="https://example.invalid/models/support-agent-demo-v1"
```

Judge, guardian, toxicity, and MLflow settings keep the `GAUSSIA_*` and `MLFLOW_*` environment variable names used by the Gaussia EvalHub provider.

### Repository structure

```text
.
├── chart/                 # Minimal Helm chart for smoke and EvalHub submit jobs
├── docs/                  # Integration notes and architecture images
├── quickstart/            # Local runners and public agent transcript fixtures
└── README.md              # Red Hat AI quickstart guide
```

## Tags

- **Title:** Evaluate agents with Gaussia and EvalHub
- **Description:** Measure AI agent conversations with Gaussia benchmarks, EvalHub jobs, and MLflow metrics on Red Hat OpenShift AI.
- **Industry:** Adopt and scale AI
- **Product:** OpenShift AI, OpenShift
- **Use case:** Agent evaluation, model observability, continuous improvement
- **Contributor org:** Alquimia AI
