# Advanced — manual Helm

Use these commands only when you cannot use the Makefile. Load `.env` first: `set -a; source .env; set +a`.

**Install — local MLflow CR** (equivalent to `make install-standalone`):

```bash
helm upgrade --install gaussia-evalhub ./deploy/helm \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set job.enabled=false
```

**Install — shared MLflow** (equivalent to `make install`):

```bash
export MLFLOW_NAMESPACE="${MLFLOW_NAMESPACE:-redhat-ods-applications}"
export MLFLOW_SERVICE="${MLFLOW_SERVICE:-mlflow}"

helm upgrade --install gaussia-evalhub ./deploy/helm \
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
helm upgrade --install gaussia-evalhub ./deploy/helm \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --set job.enabled=false \
  --set mlflow.create=false \
  --set platform.mlflow.create=false
```

**Run — humanity** (equivalent to `make run-humanity`; then `make wait-run RUN_NAME=...`):

```bash
RUN_NAME="gaussia-evalhub-run-humanity-$(date +%H%M%S)"

helm install "${RUN_NAME}" ./deploy/helm \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set ui.enabled=false \
  --set quickstart.fixture=first-line-support \
  --set quickstart.benchmarks=humanity \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="http://gaussia-evalhub-evalhub:8080" \
  --set evalhub.tenant="${NAMESPACE}" \
  --set mlflow.create=false
```

**Run — all benchmarks** (equivalent to `make upgrade-provider` + `make run-all`):

```bash
helm upgrade gaussia-evalhub ./deploy/helm \
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

helm install "${RUN_NAME}" ./deploy/helm \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set ui.enabled=false \
  --set quickstart.fixture=first-line-support \
  --set quickstart.benchmarks=auto \
  --set quickstart.uniqueRun=true \
  --set evalhub.baseUrl="http://gaussia-evalhub-evalhub:8080" \
  --set evalhub.tenant="${NAMESPACE}" \
  --set mlflow.create=false
```

**External EvalHub** (equivalent to `make install-external`):

```bash
helm install "${RUN_NAME}" ./deploy/helm \
  --namespace "${NAMESPACE}" \
  --set platform.enabled=false \
  --set ui.enabled=false \
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
  python apps/evalhub_job_submission/submit_evalhub_job.py \
    --fixture apps/evalhub_job_submission/fixtures/first-line-support.json \
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
