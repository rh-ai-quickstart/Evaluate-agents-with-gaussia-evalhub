# Measure agent quality with Gaussia and EvalHub

Use this AI quickstart on Red Hat® OpenShift® AI to evaluate agent conversations with repeatable Gaussia benchmarks, EvalHub jobs, and MLflow metrics.

## Table of contents

- [Detailed description](#detailed-description)
  - [The challenge](#the-challenge)
  - [Our solution](#our-solution)
  - [What you'll build](#what-youll-build)
  - [See it in action](#see-it-in-action)
  - [Architecture diagrams](#architecture-diagrams)
- [Requirements](#requirements)
  - [Minimum software requirements](#minimum-software-requirements)
  - [Required user permissions](#required-user-permissions)
- [Deploy](#deploy)
  - [Prerequisites](#prerequisites)
  - [Quick Start - Self-contained OpenShift run](#quick-start---self-contained-openshift-run)
  - [Run all benchmarks](#run-all-benchmarks)
  - [Use existing EvalHub and MLflow](#use-existing-evalhub-and-mlflow)
  - [OpenShift smoke job](#openshift-smoke-job)
  - [Local smoke test](#local-smoke-test)
  - [Validate results](#validate-results)
  - [Delete](#delete)
- [References](#references)
- [Technical details](#technical-details)
  - [Payload contract](#payload-contract)
  - [Benchmark selection](#benchmark-selection)
  - [Provider registration](#provider-registration)
  - [Model and run metadata](#model-and-run-metadata)
  - [Repository structure](#repository-structure)
- [Tags](#tags)

## Detailed description

This AI quickstart helps platform, product, and model teams measure agent quality with repeatable evaluation jobs. It uses Gaussia as the evaluation provider, EvalHub as the job orchestration layer, and MLflow as the metrics and run history backend.

The included scenario evaluates a first-line support agent handling an application release incident. The same pattern applies to IT service desk agents, incident response assistants, customer support agents, and internal operations agents.

### The challenge

Agentic systems are hard to assess with manual review alone. A support agent may sound helpful in one response while losing context, giving inconsistent guidance, or drifting into weaker behavior over a longer session.

Teams need a repeatable way to answer practical release questions:

- Did the new agent version preserve context across the full conversation?
- Which benchmark changed after a prompt, model, or retrieval update?
- Can product and engineering teams inspect results in the same place?
- Which model or agent version produced the evaluated transcript?

### Our solution

This quickstart turns an agent transcript into an EvalHub job and evaluates it with Gaussia benchmarks. EvalHub fans out benchmark work, the Gaussia provider computes metrics, and MLflow records the evaluated model, dataset, source, tags, metrics, and artifacts.

The primary flow is source-runtime agnostic. Any system that can produce `dataset + metadata` can create the same EvalHub job. Alquimia Runtime is documented as an optional source path, not as a dependency of the quickstart.

### What you'll build

By completing this quickstart, you will:

- Deploy a namespace-scoped evaluation stack with MLflow, EvalHub, the Gaussia provider registration, and a quickstart Job.
- Submit a live EvalHub job for a deterministic agent transcript without relying on a pre-existing EvalHub service.
- Run three benchmarks for a short transcript and five benchmarks for a longer transcript.
- Confirm EvalHub benchmark fan-out and MLflow metric tracking.
- Understand how to connect an external source system, including Alquimia Runtime, to the same evaluation flow.

### See it in action

The default smoke path runs the `humanity` benchmark against a deterministic agent transcript and prints EvalHub-compatible results:

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

When connected to EvalHub and MLflow, the long transcript creates one EvalHub job, five benchmark jobs, and one MLflow run per benchmark.

![Example EvalHub results view showing five Gaussia benchmark jobs for one evaluated agent transcript](docs/images/evalhub-results-view.svg)

![Example MLflow runs view showing dataset, source, model, and benchmark metrics populated for Gaussia evaluations](docs/images/mlflow-runs-view.svg)

### Architecture diagrams

![Architecture diagram showing an agent transcript sent to EvalHub, evaluated by the Gaussia provider, and logged to MLflow](docs/images/gaussia-evalhub-architecture.svg)

**Flow summary:**

1. A source system exports an agent transcript as a Gaussia-compatible dataset.
2. The quickstart submits an EvalHub job with one benchmark entry per selected Gaussia metric family.
3. EvalHub starts the Gaussia provider adapter with `python -m gaussia.integrations.evalhub.adapter`.
4. The provider evaluates the dataset, reports results to EvalHub, and logs metrics, datasets, sources, and model metadata to MLflow.

## Requirements

### Minimum software requirements

- Python 3.12+.
- [uv](https://docs.astral.sh/uv/) for local quickstart commands.
- Helm 3.x.
- OpenShift CLI `oc`.
- Red Hat OpenShift 4.18+.
- Red Hat OpenShift AI 2.16+ with the MLflow custom resource available.
- A public release of `gaussia[evalhub]`.
- Optional judge and guardian API credentials for model-backed benchmarks.

### Required user permissions

- Local smoke test: no cluster permissions.
- Self-contained OpenShift run: permission to create ConfigMaps, Jobs, Pods, Routes, RoleBindings, ServiceAccounts, Services, Deployments, and MLflow custom resources in the target namespace.
- Existing-service mode: EvalHub token with permission to create jobs in the configured tenant.

## Deploy

### Prerequisites

Clone the repository:

```bash
git clone https://github.com/rh-ai-quickstart/Evaluate-agents-with-gaussian-evalhub.git
cd Evaluate-agents-with-gaussian-evalhub
```

Create a namespace for the quickstart:

```bash
export NAMESPACE="gaussia-evalhub-quickstart"
oc new-project "${NAMESPACE}"
```

### Quick Start - Self-contained OpenShift run

Install the quickstart stack and submit one live EvalHub job. This creates MLflow, EvalHub, the Gaussia provider registration, and the submit Job in the same namespace:

```bash
helm install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --set mode=submit \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=humanity \
  --set quickstart.uniqueRun=true
```

Watch the job:

```bash
oc logs job/gaussia-evalhub-submit -n "${NAMESPACE}" -f
```

The default `humanity` benchmark does not require external judge or guardian credentials. It still exercises the full flow: quickstart Job, EvalHub job creation, Gaussia provider execution, and MLflow run logging.

### Run all benchmarks

To run `context`, `conversational`, `bias`, and `toxicity`, provide judge and guardian settings. These values are passed to the provider registration created by the chart:

```bash
export GAUSSIA_JUDGE_MODEL="openai/gpt-oss-20b"
export GAUSSIA_JUDGE_BASE_URL="https://api.groq.com/openai/v1"
export GAUSSIA_JUDGE_API_KEY="<judge-api-key>"
export GAUSSIA_GUARDIAN_MODEL="ibm-granite/granite-guardian-3.1-2b"
export GAUSSIA_GUARDIAN_BASE_URL="<guardian-endpoint-url>"
export GAUSSIA_GUARDIAN_API_KEY="<guardian-api-key>"
```

Kubernetes Jobs are immutable, so uninstall the previous release before changing the Job mode or benchmark settings:

```bash
helm uninstall gaussia-evalhub --namespace "${NAMESPACE}"

helm install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --set mode=submit \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=auto \
  --set quickstart.uniqueRun=true \
  --set-string platform.provider.judge.model="${GAUSSIA_JUDGE_MODEL}" \
  --set-string platform.provider.judge.baseUrl="${GAUSSIA_JUDGE_BASE_URL}" \
  --set-string platform.provider.judge.apiKey="${GAUSSIA_JUDGE_API_KEY}" \
  --set-string platform.provider.guardian.model="${GAUSSIA_GUARDIAN_MODEL}" \
  --set-string platform.provider.guardian.baseUrl="${GAUSSIA_GUARDIAN_BASE_URL}" \
  --set-string platform.provider.guardian.apiKey="${GAUSSIA_GUARDIAN_API_KEY}"
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

### Use existing EvalHub and MLflow

If your platform team already provides EvalHub, MLflow, and a registered `gaussia` provider, disable the embedded platform and point the quickstart Job at that endpoint:

```bash
export EVALHUB_BASE_URL="https://evalhub.example.com"
export EVALHUB_AUTH_TOKEN="<token>"
export EVALHUB_TENANT="default"

helm install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set mode=submit \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=auto \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="${EVALHUB_BASE_URL}" \
  --set evalhub.authToken="${EVALHUB_AUTH_TOKEN}" \
  --set evalhub.tenant="${EVALHUB_TENANT}" \
  --set evalhub.insecure=false
```

### OpenShift smoke job

Use smoke mode when you only want to verify the Gaussia EvalHub adapter in OpenShift without creating an EvalHub job:

```bash
helm install gaussia-evalhub-smoke ./chart \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set mode=smoke \
  --set quickstart.fixture=long \
  --set quickstart.benchmarks=humanity
```

### Local smoke test

Run the adapter locally with the long fixture and the `humanity` benchmark. This path does not require EvalHub, MLflow, OpenShift, judge credentials, or guardian credentials.

```bash
uv run \
  --with "gaussia[evalhub]" \
  python quickstart/local_provider_smoke.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks humanity
```

To use the benchmark selector locally, run:

```bash
uv run \
  --with "gaussia[evalhub]" \
  python quickstart/local_provider_smoke.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks auto
```

The long fixture selects `humanity`, `context`, `conversational`, `bias`, and `toxicity`. Configure the required `GAUSSIA_*` judge, guardian, and toxicity settings before running model-backed benchmarks.

You can also submit a live EvalHub job from your workstation:

```bash
uv run \
  --with "gaussia[evalhub]" \
  --with "eval-hub-sdk[client]==0.1.5" \
  python quickstart/submit_evalhub_job.py \
    --fixture quickstart/fixtures/agent_transcript_long.json \
    --benchmarks auto \
    --unique-run
```

### Validate results

Use these checks to confirm the quickstart completed:

```bash
oc get mlflow,deploy,svc,route,jobs,pods -n "${NAMESPACE}"
oc logs job/gaussia-evalhub-submit -n "${NAMESPACE}"
```

In EvalHub, confirm that the long fixture created one top-level job. With `quickstart.benchmarks=auto`, the long fixture creates five benchmark jobs.

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

### Provider registration

The Helm chart registers the Gaussia provider in EvalHub with provider id `gaussia` and this adapter command:

```bash
python -m gaussia.integrations.evalhub.adapter
```

The embedded provider runtime uses a Python base image and installs these packages before running the adapter:

```bash
python -m pip install "gaussia[evalhub]" "eval-hub-sdk[adapter]==0.1.5"
```

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
├── chart/                 # Helm chart for MLflow, EvalHub, provider registration, and quickstart jobs
├── docs/                  # Integration notes and architecture images
├── quickstart/            # Local runners and public agent transcript fixtures
└── README.md              # Red Hat AI quickstart guide
```

## Tags

- **Title:** Measure agent quality with Gaussia and EvalHub
- **Description:** Evaluate agent conversations with repeatable Gaussia benchmarks, EvalHub jobs, and MLflow metrics on Red Hat OpenShift AI.
- **Business challenge:** Adopt and scale AI
- **Product:** OpenShift AI, OpenShift
- **Use case:** Agent evaluation, model observability, continuous improvement
- **Contributor org:** Alquimia AI
