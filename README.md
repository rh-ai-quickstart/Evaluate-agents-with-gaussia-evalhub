# Scaling enterprise AI fleets with Gaussia and EvalHub

Use this AI quickstart on Red Hat® OpenShift® AI to evaluate autonomous agent conversations with repeatable [Gaussia] benchmarks, EvalHub orchestration, and MLflow run history.

## Table of contents

- [Detailed description](#detailed-description)
  - [The challenge](#the-challenge)
  - [Our solution](#our-solution)
  - [Enterprise architecture](#enterprise-architecture)
  - [Metric families](#gaussia-metric-families)
  - [What you'll build](#what-youll-build)
  - [See it in action](#see-it-in-action)
  - [Architecture diagrams](#architecture-diagrams)
- [Requirements](#requirements)
  - [Minimum software requirements](#minimum-software-requirements)
  - [Required user permissions](#required-user-permissions)
- [Deploy](#deploy)
  - [Deploy with Make](#deploy-with-make)
  - [Environment file](#environment-file)
  - [Install](#install)
  - [Run evaluations](#run-evaluations)
  - [Uninstall](#uninstall)
  - [Step 1 - Deploy judge and guardian models](#step-1---deploy-judge-and-guardian-models)
  - [Step 2 - Prepare the quickstart project](#step-2---prepare-the-quickstart-project)
  - [Step 3 - Install the evaluation platform](#step-3---install-the-evaluation-platform)
  - [Step 4 - Run the first evaluation](#step-4---run-the-first-evaluation)
  - [Step 5 - Run the full benchmark suite](#step-5---run-the-full-benchmark-suite)
  - [Step 6 - Validate results](#step-6---validate-results)
  - [Step 7 - Clean up](#step-7---clean-up)
  - [Optional - Use existing EvalHub and MLflow](#optional---use-existing-evalhub-and-mlflow)
  - [Advanced — manual Helm](#advanced--manual-helm)
  - [How it works](docs/how-it-works.md)
  - [Troubleshooting](#troubleshooting)
- [References](#references)
- [Technical details](#technical-details)
  - [Payload contract](#payload-contract)
  - [Benchmark selection](#benchmark-selection)
  - [Provider registration](#provider-registration)
  - [Model and run metadata](#model-and-run-metadata)
  - [Repository structure](#repository-structure)
- [Tags](#tags)

## Detailed description

This AI quickstart helps platform, product, and model teams measure autonomous agent quality before agent updates reach production. It uses [Gaussia] as the evaluation provider, EvalHub as the job orchestration layer, and MLflow as the metrics and run history backend.

The included scenarios evaluate agents in first-line support, retail assistance, and root-cause analysis workflows. The same pattern applies to IT service desk agents, incident response assistants, customer support agents, and internal operations agents running as part of a larger enterprise AI fleet.

### The challenge

Building one agent in a notebook is straightforward. Scaling a fleet of agents across support, retail, SRE, and internal operations workflows is a different engineering problem. Once agents execute repeated workflows for real users, manual review cannot reliably catch context loss, inconsistent guidance, safety regressions, or behavior drift across longer sessions.

Teams need a repeatable way to answer practical release and governance questions:

- Did the new agent version preserve context across the full conversation?
- Which benchmark changed after a prompt, model, or retrieval update?
- Can product and engineering teams inspect results in the same place?
- Which model or agent version produced the evaluated conversation?
- Did the agent introduce attribute-level bias, toxic language, or harmful associations that simple keyword filters would miss?

### Our solution

This quickstart turns fixture-based agent conversations into EvalHub jobs and evaluates them with [Gaussia] benchmarks. EvalHub fans out benchmark work, the [Gaussia] provider computes metrics, and MLflow records the evaluated model, dataset, source, tags, metrics, and artifacts.

The primary flow is self-contained in the Red Hat OpenShift AI environment created by the quickstart: a submit Job sends `dataset + metadata` to EvalHub, EvalHub runs the [Gaussia] provider, and MLflow stores the evaluation history. This gives teams a repeatable evaluation stack that can run inside the same OpenShift boundary as their AI workloads.

### Enterprise architecture

This quickstart demonstrates the evaluation layer of a three-tier enterprise agentic stack:

| Layer | Role in the stack | Quickstart component |
| --- | --- | --- |
| Red Hat OpenShift | Provides the enterprise Kubernetes foundation for namespace isolation, service discovery, routes, RBAC, and workload execution. | Helm-deployed services, Jobs, Routes, ServiceAccounts, and RoleBindings. |
| Red Hat OpenShift AI | Provides the MLOps layer for model endpoints, experiment tracking, and run history. | MLflow, optional judge and guardian model endpoints, and OpenShift AI model serving. |
| Automated behavioral evaluation | Converts agent conversations into repeatable benchmark jobs and records structured evaluation evidence. | EvalHub orchestration, [Gaussia] provider execution, fixture datasets, and MLflow metrics. |

The quickstart intentionally starts with public scenario fixtures instead of a live runtime dependency. That makes the evaluation pipeline easy to reproduce first. The same EvalHub, [Gaussia], and MLflow pattern can then be connected to live agent runtimes that emit conversation datasets.

### Gaussia metric families

[Gaussia] is a Python evaluation framework for measuring AI assistant and agent behavior across conversation quality, context use, safety, and response style. In this quickstart, [Gaussia] runs as an EvalHub provider: EvalHub creates one benchmark job per selected metric family, and each benchmark writes structured results to MLflow.

The quickstart currently exposes these [Gaussia] metric families through the EvalHub provider:

| Metric family | What it measures | Typical signal |
| --- | --- | --- |
| `humanity` | Emotional profile and human-like response tone using lexicon-based emotion distributions. | Emotional entropy and emotion balance across assistant responses. |
| `context` | Whether the assistant answer stays aligned with the provided conversation context. | Context-awareness score for the session. |
| `conversational` | Dialogue quality across memory, language, Grice's maxims, and sensibleness. | Multi-dimension conversational scores from an LLM judge. |
| `agentic` | Whether the evaluated agent answer matches the expected answer in ground-truth fixtures. | Correct interactions, correctness rate, `pass@k`, and `pass^k`. |
| `bias` | Potential biased behavior across protected attributes such as gender, race, religion, nationality, and sexual orientation. | Attribute-level bias rates and aggregate bias score. |
| `toxicity` | Toxic language and harmful association patterns across detected groups. | Toxicity, directed toxicity, sentiment bias, and group dispersion metrics. |

The `humanity` benchmark can run without external judge credentials. The `context`, `conversational`, `agentic`, and `bias` benchmarks require judge or guardian model settings because they use model-backed evaluation. The `toxicity` benchmark uses embedding and lexicon-based analysis.

[Gaussia] also includes additional metric families that can be used when the dataset or evaluation workflow requires a different signal. They are useful extension points for future EvalHub provider benchmarks:

| Metric family | What it measures | Typical signal |
| --- | --- | --- |
| `best_of` | Head-to-head comparison of multiple assistant responses for the same prompt or conversation. | Winning assistant id, contest history, judge confidence, verdict, and reasoning. |
| `regulatory` | Whether an assistant response is supported or contradicted by a regulatory or policy corpus. | Compliance score, verdict, supporting chunks, contradicting chunks, and retrieved evidence. |
| `vision_similarity` | Semantic similarity between a vision-language model description and human ground truth. | Mean, minimum, and maximum similarity across frames or examples. |
| `vision_hallucination` | Whether a vision-language model describes content that does not match the ground truth scene. | Hallucination rate, number of hallucinated frames, and per-frame similarity. |

### What you'll build

By completing this quickstart, you will:

- Deploy a namespace-scoped OpenShift AI evaluation stack with MLflow, EvalHub, the [Gaussia] provider registration, and quickstart Jobs.
- Submit deterministic agent conversation fixtures as EvalHub jobs without relying on a pre-existing EvalHub service.
- Run the included scenario fixtures with three default benchmarks or six benchmarks when `quickstart.benchmarks=auto`.
- Confirm EvalHub benchmark fan-out and MLflow metric tracking for evaluated agent versions, datasets, and metric families.

### See it in action

The default path submits the `first-line-support` fixture to EvalHub, runs the `humanity` benchmark with the [Gaussia] provider, and records the benchmark run in MLflow:

```json
{
  "status": "submitted",
  "job_id": "...",
  "benchmark_ids": [
    "humanity"
  ],
  "session_id": "first-line-support-agent-session-20260508184548"
}
```

The [Gaussia] provider then reports benchmark results back through EvalHub:

```json
{
  "benchmark_id": "humanity",
  "model_name": "first-line-support-demo-v1",
  "num_examples_evaluated": 10,
  "evaluation_metadata": {
    "payload_source": "dataset",
    "primary_metric_name": "humanity_assistant_emotional_entropy"
  }
}
```

With `quickstart.benchmarks=auto`, the included fixtures create one EvalHub job, six benchmark jobs, and one MLflow run per benchmark.

### Architecture diagrams

![Architecture diagram showing an agent conversation fixture submitted to EvalHub on OpenShift AI, evaluated by the Gaussia provider, and logged to MLflow](docs/images/gaussia-evalhub-architecture.svg)

**Flow summary:**

1. The quickstart loads a public agent conversation fixture as a [Gaussia]-compatible dataset.
2. The quickstart submits an EvalHub job with one benchmark entry per selected [Gaussia] metric family.
3. EvalHub starts the [Gaussia] provider adapter with `python -m gaussia.integrations.evalhub.adapter`.
4. The provider evaluates the dataset inside the OpenShift AI environment, reports results to EvalHub, and logs metrics, datasets, sources, and model metadata to MLflow.

## Requirements

### Minimum software requirements

- Python 3.12+.
- [uv](https://docs.astral.sh/uv/) for local quickstart commands.
- Helm 3.x.
- GNU Make (optional; used by the included `Makefile` for deploy commands).
- OpenShift CLI `oc`.
- Red Hat OpenShift 4.18+.
- Red Hat OpenShift AI 2.16+ with the MLflow custom resource available.
- The Gaussia EvalHub provider image pinned by the chart.
- Optional judge and guardian API credentials for model-backed benchmarks.

### Required user permissions

- Self-contained OpenShift run: permission to create ConfigMaps, Jobs, Pods, Routes, RoleBindings, ServiceAccounts, Services, Deployments, and MLflow custom resources in the target namespace.
- Existing-service flow: EvalHub token with permission to create jobs in the configured tenant.

## Deploy

The repository includes a `Makefile` that wraps Helm, `oc`, and the quickstart Python helpers. Use it for repeatable deploys from the project root.

For an overview of platform vs run releases, Kubernetes jobs, and expected MLflow output, see **[How it works](docs/how-it-works.md)**.

### Deploy with Make

**Prerequisites:** `oc`, `helm`, and `make` on your `PATH`; you are logged in to your OpenShift cluster (`oc login`). For local submit commands, install [uv](https://docs.astral.sh/uv/).

**Humanity-only quick path** (no judge or guardian models required):

```bash
git clone https://github.com/rh-ai-quickstart/Evaluate-agents-with-gaussia-evalhub.git
cd Evaluate-agents-with-gaussia-evalhub

make env-init
make install-standalone    # local MLflow CR in the quickstart namespace
make run-humanity          # submits the job and waits for benchmark completion
make validate
```

On OpenShift AI 3.4+ with shared MLflow in `redhat-ods-applications`, use `make install` instead of `make install-standalone`.

**Full benchmark suite** (requires judge and guardian values in `.env` — see [Step 1](#step-1---deploy-judge-and-guardian-models)):

```bash
make env-init              # then edit .env with judge/guardian endpoints
make env-verify-provider   # optional sanity check before run-all
make install               # shared MLflow alias (default on OpenShift AI 3.4+)
make run-all RUN_NAME=gaussia-evalhub-run-all-$(date +%H%M%S)
make validate
```

List all targets and defaults: `make help`.

### Environment file

Create and inspect `.env` before installing or running benchmarks:

```bash
make env-init              # copies .env.example → .env
make env-show              # prints loaded values (secrets masked)
make env-verify-provider   # fails if judge/guardian placeholders remain
make env-verify-external   # fails if EVALHUB_* placeholders remain (external flow)
```

The Makefile loads `.env` automatically. Judge and guardian variables can stay as placeholders for `make install` and `make run-humanity`; `make run-all` and `make upgrade-provider` require real values.

| Variable group | Required when | Purpose |
| --- | --- | --- |
| `GAUSSIA_JUDGE_*`, `GAUSSIA_GUARDIAN_*`, `GAUSSIA_AGENTIC_*` | `make run-all`, `make upgrade-provider` | Model-backed benchmarks |
| `EVALHUB_*` | `make install-external`, `make run-local` | Point at an existing EvalHub |
| `MLFLOW_TRACKING_URI` | Optional | Override shared-MLflow URI on `make upgrade-provider` |
| `GAUSSIA_EVALUATED_MODEL_*` | Optional | Override evaluated model name/URL in MLflow |

See [.env.example](.env.example) for the full template.

### Install

Install the evaluation platform **once** per namespace. This creates EvalHub, the [Gaussia] provider registration, and MLflow connectivity. Evaluation jobs are separate Helm releases installed in [Run evaluations](#run-evaluations).

| Goal | Command | When to use |
| --- | --- | --- |
| Shared MLflow (default) | `make install` | OpenShift AI 3.4+; MLflow runs in `redhat-ods-applications` (or set `MLFLOW_NAMESPACE`) |
| Local MLflow CR | `make install-standalone` | Self-contained namespace with its own `mlflow` CR (OpenShift AI 2.16 path) |
| Existing MLflow CR in namespace | `make install-no-mlflow` | Target namespace already has an MLflow instance named `mlflow` |
| Shared MLflow alias | `make install-shared-mlflow` | Alias for `make install` |

All install targets create the namespace when needed (`make namespace`), disable the bundled submit Job (`job.enabled=false`), and wait for EvalHub (`make wait-evalhub`). When judge and guardian values are present in `.env`, they are applied to the provider registration at install time.

**Overrides** (append to any install command):

| Variable | Default | Purpose |
| --- | --- | --- |
| `NAMESPACE` | `gaussia-evalhub-quickstart` | OpenShift project |
| `RELEASE` | `gaussia-evalhub` | Helm release name for the platform stack |
| `MLFLOW_NAMESPACE` | `redhat-ods-applications` | Namespace of the shared MLflow service |
| `MLFLOW_SERVICE` | `mlflow` | Shared MLflow Kubernetes service name |

After install, confirm EvalHub and MLflow are reachable:

```bash
make wait-evalhub
make validate
```

For manual `helm`/`oc` commands without Make, see [Advanced — manual Helm](#advanced--manual-helm).

### Run evaluations

Each evaluation is a **separate Helm release** that submits one EvalHub job and runs selected benchmarks. `make run-humanity` and `make run-all` call `quickstart/wait_run.py` to wait for the submit Job and benchmark Jobs to finish.

| Goal | Command | Notes |
| --- | --- | --- |
| Humanity benchmark only | `make run-humanity` | No judge/guardian required; optional `FIXTURE=retail`, `RUN_NAME=my-run` |
| All benchmarks | `make run-all` | Runs `upgrade-provider` first, then waits for six benchmarks |
| Existing EvalHub | `make install-external` | Set `EVALHUB_*` in `.env`; runs `auto` benchmarks and waits |
| Submit from workstation | `make run-local` | Uses `uv` and `quickstart/submit_evalhub_job.py` |

**Run overrides:**

| Variable | Default | Purpose |
| --- | --- | --- |
| `FIXTURE` | `first-line-support` | Scenario fixture (`retail`, `root-cause-analysis`) |
| `RUN_NAME` | timestamped | Per-run Helm release name (print at end of `make run-*`) |

Follow submit logs for a run release:

```bash
make logs RUN_NAME=<name-from-run-output>
```

Re-run or wait manually:

```bash
make wait-run RUN_NAME=<name>
make list-releases
make validate
```

See [Step 4](#step-4---run-the-first-evaluation) and [Step 5](#step-5---run-the-full-benchmark-suite) for step-by-step run instructions.

### Uninstall

Remove resources in this order:

**1. Run releases** (one per `make run-humanity`, `make run-all`, or `make install-external`):

```bash
make list-releases
make uninstall-run RUN_NAME=<your-run-release>
```

**2. Platform release** (EvalHub, provider registration, MLflow alias or CR):

```bash
make uninstall
```

**3. Namespace** (destructive — removes the OpenShift project and any remaining Helm releases):

```bash
make cleanup-namespace
```

See also [Step 7 - Clean up](#step-7---clean-up).

### Step 1 - Deploy judge and guardian models

The default `humanity` benchmark can run without external model endpoints. To run the full benchmark set, deploy a judge model and a guardian model in Red Hat OpenShift AI before installing this quickstart. The models named below are suggested examples, not hard requirements. You can use different models if they expose compatible endpoints and produce stable responses for the benchmark role.

| Model role | Used by | Deployment requirement |
| --- | --- | --- |
| Judge model | `context`, `conversational`, and `agentic` | OpenAI-compatible chat completions endpoint exposed at `/v1`. |
| Guardian model | `bias` | OpenAI-compatible chat completions endpoint exposed at `/v1`. |

Deploy the suggested judge model:

1. In OpenShift AI, open the model catalog and search for `gpt-oss-20b`.
2. Open the model detail page and select **Deploy model**.
3. Use model location `URI` with `oci://registry.redhat.io/rhelai1/modelcar-gpt-oss-20b:1.5`.
4. Set model type to `Generative AI model (Example: LLM)`.
5. Review the deployment settings, deploy the model, and wait until the endpoint is ready.
6. Copy the model route, token, and served model name.

Deploy the suggested guardian model:

1. Download the `ibm-granite/granite-guardian-3.1-2b` model artifacts and upload them to S3-compatible object storage, such as MinIO.
2. In the OpenShift AI project, create an S3-compatible data connection that points to the bucket and path containing the guardian model.
3. Deploy a model from the existing data connection and set model type to `Generative AI model (Example: LLM)`.
4. Use a vLLM/KServe serving runtime with a GPU-capable hardware profile.
5. Enable the external route and token authentication.
6. Wait until the endpoint is ready, then copy the model route, token, and served model name.

Add the resulting values to `.env`:

```bash
GAUSSIA_JUDGE_MODEL="<judge-served-model-name>"
GAUSSIA_JUDGE_MODEL_PROVIDER="openai"
GAUSSIA_JUDGE_BASE_URL="https://<judge-route>/v1"
GAUSSIA_JUDGE_API_KEY="<judge-token>"
GAUSSIA_JUDGE_USE_STRUCTURED_OUTPUT="false"

GAUSSIA_GUARDIAN_MODEL="<guardian-served-model-name>"
GAUSSIA_GUARDIAN_TOKENIZER_MODEL="ibm-granite/granite-guardian-3.1-2b"
GAUSSIA_GUARDIAN_BASE_URL="https://<guardian-route>/v1"
GAUSSIA_GUARDIAN_API_KEY="<guardian-token>"
GAUSSIA_GUARDIAN_CHAT_COMPLETIONS="true"
```

Set `GAUSSIA_JUDGE_MODEL_PROVIDER` to the LangChain provider that matches your judge endpoint. Use `openai` for OpenShift AI or LiteLLM routes that expose an OpenAI-compatible `/v1` API. Custom served model names such as `llama-scout-17b` require this setting because LangChain cannot infer the provider from the model name alone.

If you already have compatible judge and guardian endpoints, use those values instead.

### Step 2 - Prepare the quickstart project

Clone the repository:

```bash
git clone https://github.com/rh-ai-quickstart/Evaluate-agents-with-gaussia-evalhub.git
cd Evaluate-agents-with-gaussia-evalhub
```

Create and inspect the environment file:

```bash
make env-init
make env-show
```

Edit `.env` with your service URLs and credentials. The Makefile and local submitter load `.env` automatically.

Create or select the OpenShift namespace:

```bash
make namespace
```

Optional override: `make namespace NAMESPACE=my-eval-namespace`

Available fixtures:

| Fixture | Scenario | Interactions |
| --- | --- | --- |
| `first-line-support` | IT first-line support troubleshooting | 10 |
| `retail` | Retail shopping and support assistant | 10 |
| `root-cause-analysis` | SRE root-cause analysis assistant | 10 |

### Step 3 - Install the evaluation platform

Install the quickstart platform once. This creates EvalHub, the [Gaussia] provider registration, and MLflow connectivity. Evaluation jobs are separate releases installed in the next steps.

| Path | Command |
| --- | --- |
| Shared MLflow (OpenShift AI 3.4+) | `make install` |
| Local MLflow CR in the namespace | `make install-standalone` |
| Namespace already has `mlflow` CR | `make install-no-mlflow` |

Override shared MLflow location when needed:

```bash
make install MLFLOW_NAMESPACE=redhat-ods-applications MLFLOW_SERVICE=mlflow
```

When judge and guardian values are in `.env`, they are applied at install time. To refresh provider settings later without a new run, use `make upgrade-provider`.

Wait for EvalHub before running an evaluation:

```bash
make wait-evalhub
make validate
```

If MLflow connectivity fails on the shared-MLflow path, confirm the alias service exists:

```bash
oc get svc mlflow -n "${NAMESPACE:-gaussia-evalhub-quickstart}"
```

To locate shared MLflow in your cluster (no Make equivalent):

```bash
oc get svc -A | grep -i mlflow
oc get mlflow -A
```

### Step 4 - Run the first evaluation

Submit a humanity-only evaluation against the installed EvalHub service:

```bash
make run-humanity
```

Optional overrides:

```bash
make run-humanity FIXTURE=retail RUN_NAME=my-humanity-run
```

`make run-humanity` installs the run release, waits for the submit Job and benchmark Job to finish, and prints the run release name.

Follow submit logs or re-wait for an existing run:

```bash
make logs RUN_NAME=<name-from-run-output>
make wait-run RUN_NAME=<name>
```

The default `humanity` benchmark does not require external judge or guardian credentials. It still exercises the full flow: quickstart Job, EvalHub job creation, [Gaussia] provider execution, and MLflow run logging.

Use a new `RUN_NAME` for each run, or remove the previous run first: `make uninstall-run RUN_NAME=...`

### Step 5 - Run the full benchmark suite

Complete [Step 1](#step-1---deploy-judge-and-guardian-models) and fill judge and guardian values in `.env`, then verify:

```bash
make env-verify-provider
```

Run all benchmarks (`make run-all` applies provider settings from `.env`, submits the job, and waits for completion):

```bash
make run-all RUN_NAME=gaussia-evalhub-run-all-$(date +%H%M%S)
```

Optional overrides: `FIXTURE=retail`, or run provider update separately before a manual re-run:

```bash
make upgrade-provider
make run-all RUN_NAME=my-run-all
```

Expected submit output includes:

```json
{
  "status": "submitted",
  "job_id": "...",
  "benchmark_ids": [
    "humanity",
    "context",
    "conversational",
    "agentic",
    "bias",
    "toxicity"
  ]
}
```

### Step 6 - Validate results

Use these checks to confirm the quickstart completed:

```bash
make validate
make logs RUN_NAME=<your-run-release>
```

In EvalHub, confirm that the selected fixture created one top-level job. With `quickstart.benchmarks=auto`, the included fixtures create six benchmark jobs.

In MLflow, confirm that each benchmark run includes:

- dataset name beginning with `gaussia-`.
- source name `gaussia.integrations.evalhub.adapter`.
- evaluated model name from fixture metadata, or from `GAUSSIA_EVALUATED_MODEL_NAME` when you override it.
- tags for `assistant_id`, `session_id`, `stream_id`, and `control_id`.

Expected results:

![Expected MLflow runs table showing benchmark runs with dataset, source, evaluated model, and metric pack columns populated](docs/images/mlflow-expected-runs-table.png)

![Expected MLflow chart view grouped by metric pack with context and conversational metrics](docs/images/mlflow-expected-metric-charts.png)

### Step 7 - Clean up

See [Uninstall](#uninstall). Summary:

```bash
make list-releases
make uninstall-run RUN_NAME=<your-run-release>
make uninstall
make cleanup-namespace   # optional; deletes the OpenShift project
```

### Optional - Use existing EvalHub and MLflow

If your platform team already provides EvalHub, MLflow, and a registered `gaussia` provider, configure `EVALHUB_*` in `.env`, then:

```bash
make env-verify-external
make install-external FIXTURE=first-line-support RUN_NAME=my-external-run
```

Submit from your workstation instead of a cluster Job:

```bash
make run-local FIXTURE=first-line-support
```

### Advanced — manual Helm

Use these commands only when you cannot use the Makefile. Load `.env` first: `set -a; source .env; set +a`.

**Install — local MLflow CR** (equivalent to `make install-standalone`):

```bash
helm upgrade --install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set job.enabled=false
```

**Install — shared MLflow** (equivalent to `make install`):

```bash
export MLFLOW_NAMESPACE="${MLFLOW_NAMESPACE:-redhat-ods-applications}"
export MLFLOW_SERVICE="${MLFLOW_SERVICE:-mlflow}"

helm upgrade --install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set job.enabled=false \
  --set mlflow.create=false \
  --set platform.mlflow.create=false \
  --set platform.mlflow.serviceAlias.enabled=true \
  --set platform.mlflow.serviceAlias.externalName="${MLFLOW_SERVICE}.${MLFLOW_NAMESPACE}.svc.cluster.local" \
  --set platform.mlflow.trackingUri="https://mlflow.${MLFLOW_NAMESPACE}.svc.cluster.local:8443" \
  --set platform.mlflow.workspace="${NAMESPACE}" \
  --set platform.mlflow.rbacNamespace="${NAMESPACE}"
```

**Install — existing `mlflow` CR in namespace** (equivalent to `make install-no-mlflow`):

```bash
helm upgrade --install gaussia-evalhub ./chart \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set job.enabled=false \
  --set mlflow.create=false \
  --set platform.mlflow.create=false
```

**Run — humanity** (equivalent to `make run-humanity`; then `make wait-run RUN_NAME=...`):

```bash
RUN_NAME="gaussia-evalhub-run-humanity-$(date +%H%M%S)"

helm install "${RUN_NAME}" ./chart \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set quickstart.fixture=first-line-support \
  --set quickstart.benchmarks=humanity \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="http://gaussia-evalhub-evalhub:8080" \
  --set evalhub.tenant="${NAMESPACE}" \
  --set mlflow.create=false
```

**Run — all benchmarks** (equivalent to `make upgrade-provider` + `make run-all`):

```bash
helm upgrade gaussia-evalhub ./chart \
  --reuse-values \
  --namespace "${NAMESPACE}" \
  --set job.enabled=false \
  --set mlflow.create=false \
  --set platform.mlflow.create=false \
  --set platform.mlflow.serviceAlias.enabled=true \
  --set platform.mlflow.serviceAlias.externalName="${MLFLOW_SERVICE}.${MLFLOW_NAMESPACE}.svc.cluster.local" \
  --set platform.mlflow.trackingUri="https://mlflow.${MLFLOW_NAMESPACE}.svc.cluster.local:8443" \
  --set-string platform.provider.judge.model="${GAUSSIA_JUDGE_MODEL}" \
  --set-string platform.provider.judge.modelProvider="${GAUSSIA_JUDGE_MODEL_PROVIDER:-openai}" \
  --set-string platform.provider.judge.baseUrl="${GAUSSIA_JUDGE_BASE_URL}" \
  --set-string platform.provider.judge.apiKey="${GAUSSIA_JUDGE_API_KEY}" \
  --set-string platform.provider.guardian.model="${GAUSSIA_GUARDIAN_MODEL}" \
  --set-string platform.provider.guardian.tokenizerModel="${GAUSSIA_GUARDIAN_TOKENIZER_MODEL}" \
  --set-string platform.provider.guardian.baseUrl="${GAUSSIA_GUARDIAN_BASE_URL}" \
  --set-string platform.provider.guardian.apiKey="${GAUSSIA_GUARDIAN_API_KEY}" \
  --set-string platform.provider.guardian.chatCompletions="${GAUSSIA_GUARDIAN_CHAT_COMPLETIONS}" \
  --set-string platform.provider.agentic.k="${GAUSSIA_AGENTIC_K}" \
  --set-string platform.provider.agentic.threshold="${GAUSSIA_AGENTIC_THRESHOLD}" \
  --set-string platform.provider.agentic.toolThreshold="${GAUSSIA_AGENTIC_TOOL_THRESHOLD}"

oc rollout restart deploy/gaussia-evalhub-evalhub -n "${NAMESPACE}"
oc rollout status deploy/gaussia-evalhub-evalhub -n "${NAMESPACE}"

RUN_NAME="gaussia-evalhub-run-all-$(date +%H%M%S)"

helm install "${RUN_NAME}" ./chart \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set quickstart.fixture=first-line-support \
  --set quickstart.benchmarks=auto \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="http://gaussia-evalhub-evalhub:8080" \
  --set evalhub.tenant="${NAMESPACE}" \
  --set mlflow.create=false
```

**External EvalHub** (equivalent to `make install-external`):

```bash
helm install "${RUN_NAME}" ./chart \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set quickstart.fixture=first-line-support \
  --set quickstart.benchmarks=auto \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="${EVALHUB_BASE_URL}" \
  --set evalhub.authToken="${EVALHUB_AUTH_TOKEN}" \
  --set evalhub.tenant="${EVALHUB_TENANT}" \
  --set evalhub.insecure=false
```

**Local submit** (equivalent to `make run-local`):

```bash
uv run \
  --with "gaussia[evalhub]" \
  --with "eval-hub-sdk[client]==0.1.5" \
  python quickstart/submit_evalhub_job.py \
    --fixture quickstart/fixtures/first-line-support.json \
    --benchmarks auto \
    --unique-run
```

**Uninstall** (equivalent to `make uninstall-run`, `make uninstall`, `make cleanup-namespace`):

```bash
helm list --namespace "${NAMESPACE}"
helm uninstall "${RUN_NAME}" --namespace "${NAMESPACE}"
helm uninstall gaussia-evalhub --namespace "${NAMESPACE}"
oc delete project "${NAMESPACE}"
```

### Troubleshooting

#### EvalHub returns `400 Bad Request` when submitting a job

Check the EvalHub pod logs first:

```bash
oc logs deploy/gaussia-evalhub-evalhub -n "${NAMESPACE}"
```

If the log includes an error like this, the failure is MLflow connectivity, not the evaluation payload:

```text
lookup mlflow.<namespace>.svc ... no such host
```

Verify the MLflow service that EvalHub is configured to use:

```bash
helm get values gaussia-evalhub -n "${NAMESPACE}" --all | grep -E "mlflow|trackingUri|serviceAlias|rbacNamespace|workspace" -A3 -B3
oc get svc -A | grep -i mlflow
oc get mlflow -A
```

For the self-contained path, EvalHub should use the MLflow service in the quickstart namespace:

```text
https://mlflow.<quickstart-namespace>.svc:8443
```

For shared MLflow, run `make install` (or reinstall with `MLFLOW_NAMESPACE` set correctly) so the local `mlflow` service alias is created in the quickstart namespace.

## References

- [Gaussia documentation](https://github.com/gaussia-labs/pygaussia)
- [EvalHub provider adapter entrypoint](https://github.com/gaussia-labs/pygaussia)
- [Red Hat AI quickstarts catalog](https://docs.redhat.com/en/learn/ai-quickstarts)

## Technical details

### Payload contract

The public quickstart uses the preferred EvalHub provider contract:

```json
{
  "parameters": {
    "dataset": {
      "session_id": "first-line-support-agent-session",
      "assistant_id": "first-line-support-agent",
      "language": "english",
      "context": "The agent supports first-line IT troubleshooting.",
      "conversation": []
    },
    "metadata": {
      "stream_id": "first-line-support-stream",
      "control_id": "first-line-support-control",
      "source": "gaussia.quickstart.scenario-fixture.v1"
    }
  }
}
```

### Benchmark selection

The quickstart selector always includes:

- `humanity`
- `context`
- `conversational`

When the dataset has five or more interactions, it also includes:

- `bias`
- `toxicity`

When every interaction includes `ground_truth_assistant`, it also includes:

- `agentic`

Use `make run-humanity` when you want the full EvalHub, [Gaussia], and MLflow flow without judge or guardian credentials.

### Provider registration

The Helm chart registers the [Gaussia] provider in EvalHub with provider id `gaussia` and this adapter command:

```bash
python -m gaussia.integrations.evalhub.adapter
```

The provider container runs the [Gaussia] EvalHub adapter with:

```bash
python -m gaussia.integrations.evalhub.adapter
```

By default, the chart uses `docker.io/alquimiaai/gaussia-provider:1.0.0b2`, which includes the [Gaussia] EvalHub adapter, and also pins `gaussia[evalhub]==1.0.0b2` at startup so benchmark dependencies stay explicit.
Override `platform.provider.packageSpec` and `platform.provider.evalhubSdkSpec` only when you want the provider pod to install a different provider package at startup.
Use `platform.provider.image.fullReference` when you need to pin the provider to an internal image registry digest.

### Model and run metadata

The evaluated model is the agent or model version represented by the fixture, not the judge model used by a benchmark. Set these in `.env` or export them before `make run-*`:

```bash
export GAUSSIA_EVALUATED_MODEL_NAME="custom-agent-demo-v1"
export GAUSSIA_EVALUATED_MODEL_URL="https://example.invalid/models/custom-agent-demo-v1"
```

Judge, guardian, agentic, toxicity, and MLflow settings keep the `GAUSSIA_*` and `MLFLOW_*` environment variable names used by the [Gaussia] EvalHub provider.

### Repository structure

```text
.
├── .env.example           # Environment template (EvalHub, MLflow, judge, guardian)
├── Makefile               # Install, run, wait, validate, and uninstall targets
├── chart/                 # Helm chart for MLflow, EvalHub, provider registration, and quickstart jobs
├── docs/                  # Architecture images and how-it-works guide
│   └── how-it-works.md    # What is deployed, run, and evaluated
├── quickstart/            # Submitter, env checks, run waiter, and scenario fixtures
│   ├── check_env.py       # Inspect and verify .env (make env-show, env-verify-*)
│   ├── wait_run.py        # Wait for submit and benchmark jobs (make wait-run)
│   └── submit_evalhub_job.py
└── README.md              # Red Hat AI quickstart guide
```

## Tags

- **Title:** Scaling enterprise AI fleets with Gaussia and EvalHub
- **Description:** Evaluate autonomous agent conversations with repeatable [Gaussia] benchmarks, EvalHub orchestration, and MLflow run history on Red Hat OpenShift AI.
- **Business challenge:** Adopt and scale AI
- **Product:** OpenShift AI, OpenShift
- **Use case:** Agent evaluation, model observability, governance, continuous improvement
- **Contributor org:** Alquimia AI

[Gaussia]: https://github.com/gaussia-labs/pygaussia
