# Gaussia EvalHub quickstart — OpenShift / Helm deployment targets.
# See README.md "Deploy" for prerequisites, install, run, and uninstall.

SHELL := /bin/bash
.DEFAULT_GOAL := help

CHART_DIR          ?= ./chart
RELEASE            ?= gaussia-evalhub
NAMESPACE          ?= gaussia-evalhub-quickstart
MLFLOW_NAMESPACE   ?= redhat-ods-applications
MLFLOW_SERVICE     ?= mlflow
FIXTURE            ?= first-line-support
EVALHUB_SVC        ?= http://gaussia-evalhub-evalhub:8080
JOB_CPU_REQUEST    ?= 250m
JOB_MEMORY_REQUEST ?= 512Mi
JOB_CPU_LIMIT      ?= 1
JOB_MEMORY_LIMIT   ?= 1Gi

RUN_NAME ?= gaussia-evalhub-run-$(shell date +%Y%m%d%H%M%S)

# Source .env for helm/oc recipes (matches README: set -a; source .env; set +a).
define with_env
	set -a; \
	if [[ -f .env ]]; then source .env; else echo "Warning: .env not found — run: make env-init" >&2; fi; \
	set +a; \
	$(1)
endef

# Shared MLflow alias install (OpenShift AI 3.4+).
HELM_SHARED_MLFLOW_SETS := \
	--set mlflow.create=false \
	--set platform.mlflow.create=false \
	--set platform.mlflow.serviceAlias.enabled=true \
	--set platform.mlflow.serviceAlias.externalName="$(MLFLOW_SERVICE).$(MLFLOW_NAMESPACE).svc.cluster.local" \
	--set platform.mlflow.trackingUri="https://mlflow.$(MLFLOW_NAMESPACE).svc.cluster.local:8443" \
	--set platform.mlflow.workspace="$(NAMESPACE)" \
	--set platform.mlflow.rbacNamespace="$(NAMESPACE)"

# Helm --set-string flags for judge/guardian provider settings sourced from .env.
HELM_PROVIDER_SETS := \
	--set-string platform.provider.packageSpec="$${GAUSSIA_PROVIDER_PACKAGE_SPEC:-gaussia[evalhub]==1.1.0b2 langchain-openai}" \
	--set-string platform.provider.judge.model="$${GAUSSIA_JUDGE_MODEL}" \
	--set-string platform.provider.judge.modelProvider="$${GAUSSIA_JUDGE_MODEL_PROVIDER:-openai}" \
	--set-string platform.provider.judge.baseUrl="$${GAUSSIA_JUDGE_BASE_URL}" \
	--set-string platform.provider.judge.apiKey="$${GAUSSIA_JUDGE_API_KEY}" \
	--set-string platform.provider.judge.temperature="$${GAUSSIA_JUDGE_TEMPERATURE}" \
	--set-string platform.provider.judge.bosJsonClause="$${GAUSSIA_JUDGE_BOS_JSON_CLAUSE}" \
	--set-string platform.provider.judge.eosJsonClause="$${GAUSSIA_JUDGE_EOS_JSON_CLAUSE}" \
	--set-string platform.provider.judge.useStructuredOutput="$${GAUSSIA_JUDGE_USE_STRUCTURED_OUTPUT}" \
	--set-string platform.provider.guardian.model="$${GAUSSIA_GUARDIAN_MODEL}" \
	--set-string platform.provider.guardian.tokenizerModel="$${GAUSSIA_GUARDIAN_TOKENIZER_MODEL}" \
	--set-string platform.provider.guardian.baseUrl="$${GAUSSIA_GUARDIAN_BASE_URL}" \
	--set-string platform.provider.guardian.apiKey="$${GAUSSIA_GUARDIAN_API_KEY}" \
	--set-string platform.provider.guardian.temperature="$${GAUSSIA_GUARDIAN_TEMPERATURE}" \
	--set-string platform.provider.guardian.logprobs="$${GAUSSIA_GUARDIAN_LOGPROBS}" \
	--set-string platform.provider.guardian.chatCompletions="$${GAUSSIA_GUARDIAN_CHAT_COMPLETIONS}" \
	--set-string platform.provider.agentic.k="$${GAUSSIA_AGENTIC_K}" \
	--set-string platform.provider.agentic.threshold="$${GAUSSIA_AGENTIC_THRESHOLD}" \
	--set-string platform.provider.agentic.toolThreshold="$${GAUSSIA_AGENTIC_TOOL_THRESHOLD}"

.PHONY: help env-init env-check env-show env-verify-provider env-verify-external namespace \
	install install-standalone install-no-mlflow install-shared-mlflow \
	wait-evalhub upgrade-provider wait-run \
	run-humanity run-all validate logs \
	list-releases uninstall-run uninstall cleanup-namespace \
	run-local install-external

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make [target]\n\nTargets:\n"} \
		/^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-28s %s\n", $$1, $$2} \
		/^##@/ {printf "\n%s\n", substr($$0, 5)}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Common variables (override on the command line):"
	@echo "  NAMESPACE=$(NAMESPACE)"
	@echo "  RELEASE=$(RELEASE)"
	@echo "  FIXTURE=$(FIXTURE)"
	@echo "  RUN_NAME=$(RUN_NAME)"
	@echo "  MLFLOW_NAMESPACE=$(MLFLOW_NAMESPACE)"
	@echo "  JOB_CPU_REQUEST=$(JOB_CPU_REQUEST)"
	@echo "  JOB_MEMORY_REQUEST=$(JOB_MEMORY_REQUEST)"
	@echo "  JOB_CPU_LIMIT=$(JOB_CPU_LIMIT)"
	@echo "  JOB_MEMORY_LIMIT=$(JOB_MEMORY_LIMIT)"

##@ Setup

env-init: ## Copy .env.example to .env
	@test -f .env || cp .env.example .env
	@echo "Created .env — edit it with EvalHub, MLflow, judge, and guardian settings."

env-check: ## Ensure .env exists (creates from .env.example when missing)
	@test -f .env || cp .env.example .env
	@test -f .env || (echo "Missing .env — run: make env-init" && exit 1)

env-show: env-check ## Show variables loaded from .env (secrets masked)
	@$(call with_env,python3 quickstart/check_env.py show)

env-verify-provider: env-check ## Fail if judge/guardian .env values are missing or placeholders
	@$(call with_env,python3 quickstart/check_env.py verify-provider)

env-verify-external: env-check ## Fail if external EvalHub .env values are missing or placeholders
	@$(call with_env,python3 quickstart/check_env.py verify-external)

namespace: env-check ## Create or select the OpenShift project
	@oc get project "$(NAMESPACE)" >/dev/null 2>&1 || oc new-project "$(NAMESPACE)"
	@oc project "$(NAMESPACE)"

##@ Install (once)

install: env-check namespace ## Install EvalHub with shared MLflow (applies judge/guardian from .env when set)
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--create-namespace \
		--set job.enabled=false \
		$(HELM_SHARED_MLFLOW_SETS) \
		$(HELM_PROVIDER_SETS))
	@oc rollout restart deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)" 2>/dev/null || true
	@$(MAKE) wait-evalhub

install-standalone: env-check namespace ## Install EvalHub with a local MLflow CR in the namespace
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--create-namespace \
		--set job.enabled=false \
		$(HELM_PROVIDER_SETS))
	@$(MAKE) wait-evalhub

install-no-mlflow: env-check namespace ## Install when namespace already has an MLflow CR named mlflow
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--create-namespace \
		--set job.enabled=false \
		--set mlflow.create=false \
		--set platform.mlflow.create=false \
		$(HELM_PROVIDER_SETS))
	@oc rollout restart deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)" 2>/dev/null || true
	@$(MAKE) wait-evalhub

install-shared-mlflow: install ## Alias for the default shared-MLflow install

wait-evalhub: ## Wait until the EvalHub deployment is ready
	@oc rollout status deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)"

upgrade-provider: env-check env-verify-provider ## Apply judge/guardian settings from .env to the Helm release
	@$(call with_env,helm upgrade "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--reuse-values \
		--set job.enabled=false \
		$(HELM_SHARED_MLFLOW_SETS) \
		--set-string platform.mlflow.trackingUri="$${MLFLOW_TRACKING_URI:-https://mlflow.$(MLFLOW_NAMESPACE).svc.cluster.local:8443}" \
		$(HELM_PROVIDER_SETS))
	@oc rollout restart deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)"
	@$(MAKE) wait-evalhub

wait-run: ## Wait for a run submit job and EvalHub benchmark jobs (set RUN_NAME)
	@test "$(origin RUN_NAME)" != "file" || (echo "Set RUN_NAME, e.g. make wait-run RUN_NAME=gaussia-evalhub-run-all-120000" && exit 1)
	@python3 quickstart/wait_run.py --namespace "$(NAMESPACE)" --run-name "$(RUN_NAME)"

##@ Evaluation runs

run-humanity: env-check ## Submit a humanity-only quickstart job (no judge/guardian required)
	@$(call with_env,helm install "$(RUN_NAME)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set platform.enabled=false \
		--set mlflow.create=false \
		--set quickstart.fixture="$(FIXTURE)" \
		--set quickstart.benchmarks=humanity \
		--set quickstart.uniqueRun=true \
		--set evalhub.baseUrl="$(EVALHUB_SVC)" \
		--set evalhub.tenant="$(NAMESPACE)" \
		--set resources.requests.cpu="$(JOB_CPU_REQUEST)" \
		--set resources.requests.memory="$(JOB_MEMORY_REQUEST)" \
		--set resources.limits.cpu="$(JOB_CPU_LIMIT)" \
		--set resources.limits.memory="$(JOB_MEMORY_LIMIT)")
	@echo "Run release: $(RUN_NAME)"
	@$(MAKE) wait-run RUN_NAME="$(RUN_NAME)"

run-all: env-check env-verify-provider upgrade-provider ## Submit all benchmarks and wait for completion
	@$(call with_env,helm install "$(RUN_NAME)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set platform.enabled=false \
		--set mlflow.create=false \
		--set quickstart.fixture="$(FIXTURE)" \
		--set quickstart.benchmarks=auto \
		--set quickstart.uniqueRun=true \
		--set evalhub.baseUrl="$(EVALHUB_SVC)" \
		--set evalhub.tenant="$(NAMESPACE)" \
		--set resources.requests.cpu="$(JOB_CPU_REQUEST)" \
		--set resources.requests.memory="$(JOB_MEMORY_REQUEST)" \
		--set resources.limits.cpu="$(JOB_CPU_LIMIT)" \
		--set resources.limits.memory="$(JOB_MEMORY_LIMIT)")
	@echo "Run release: $(RUN_NAME)"
	@$(MAKE) wait-run RUN_NAME="$(RUN_NAME)"

install-external: env-check env-verify-external namespace ## Job-only install against existing EvalHub (uses EVALHUB_* from .env)
	@$(call with_env,helm install "$(RUN_NAME)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set platform.enabled=false \
		--set mlflow.create=false \
		--set quickstart.fixture="$(FIXTURE)" \
		--set quickstart.benchmarks=auto \
		--set quickstart.uniqueRun=true \
		--set evalhub.baseUrl="$${EVALHUB_BASE_URL}" \
		--set evalhub.authToken="$${EVALHUB_AUTH_TOKEN}" \
		--set evalhub.tenant="$${EVALHUB_TENANT}" \
		--set evalhub.insecure=false \
		--set resources.requests.cpu="$(JOB_CPU_REQUEST)" \
		--set resources.requests.memory="$(JOB_MEMORY_REQUEST)" \
		--set resources.limits.cpu="$(JOB_CPU_LIMIT)" \
		--set resources.limits.memory="$(JOB_MEMORY_LIMIT)")
	@$(MAKE) wait-run RUN_NAME="$(RUN_NAME)"

run-local: env-check env-verify-external ## Submit a job from your workstation with uv (existing EvalHub)
	@$(call with_env,uv run \
		--with "gaussia[evalhub]" \
		--with "eval-hub-sdk[client]==0.1.5" \
		python quickstart/submit_evalhub_job.py \
		--fixture "quickstart/fixtures/$(FIXTURE).json" \
		--benchmarks auto \
		--unique-run)

##@ Verify and clean up

validate: ## List platform resources in the namespace
	@oc get mlflow,deploy,svc,route,jobs,pods -n "$(NAMESPACE)"

logs: ## Follow logs for a run submit job (set RUN_NAME)
	@test "$(origin RUN_NAME)" != "file" || (echo "Set RUN_NAME, e.g. make logs RUN_NAME=gaussia-evalhub-run-humanity-120000" && exit 1)
	@oc logs "job/$(RUN_NAME)-submit" -n "$(NAMESPACE)" -f

list-releases: ## List Helm releases in the namespace
	@helm list --namespace "$(NAMESPACE)"

uninstall-run: ## Remove a run release (set RUN_NAME)
	@test "$(origin RUN_NAME)" != "file" || (echo "Set RUN_NAME" && exit 1)
	@helm uninstall "$(RUN_NAME)" --namespace "$(NAMESPACE)"

uninstall: ## Remove the Helm release (EvalHub, provider, MLflow)
	@if helm status "$(RELEASE)" -n "$(NAMESPACE)" >/dev/null 2>&1; then \
		helm uninstall "$(RELEASE)" -n "$(NAMESPACE)"; \
	else \
		echo "Helm release $(RELEASE) not found in $(NAMESPACE) — nothing to uninstall"; \
	fi

cleanup-namespace: uninstall ## Delete the OpenShift project (destructive)
	@export NAMESPACE="$(NAMESPACE)"; \
	helm uninstall "$(RELEASE)" -n "$(NAMESPACE)" 2>/dev/null || true; \
	for release in $(helm list -n "$(NAMESPACE)" -q); do \
		helm uninstall "$(release)" -n "$(NAMESPACE)"; \
	done; \
	oc delete project "$(NAMESPACE)"
