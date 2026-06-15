# Gaussia EvalHub quickstart — OpenShift / Helm deployment targets.
# See README.md "Deploy with Make" for prerequisites and usage.

SHELL := /bin/bash
.DEFAULT_GOAL := help

CHART_DIR        ?= ./chart
RELEASE          ?= gaussia-evalhub
NAMESPACE        ?= gaussia-evalhub-quickstart
MLFLOW_NAMESPACE ?= redhat-ods-applications
FIXTURE          ?= first-line-support
EVALHUB_SVC      ?= http://gaussia-evalhub-evalhub:8080

RUN_NAME ?= gaussia-evalhub-run-$(shell date +%Y%m%d%H%M%S)

# Source .env for helm/oc recipes (matches README: set -a; source .env; set +a).
define with_env
	set -a; \
	if [[ -f .env ]]; then source .env; else echo "Warning: .env not found — copy from .env.example (make env-init)" >&2; fi; \
	set +a; \
	$(1)
endef

.PHONY: help env-init env-check namespace \
	install install-no-mlflow install-shared-mlflow \
	wait-evalhub upgrade-provider \
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

##@ Setup

env-init: ## Copy .env.example to .env
	@test -f .env || cp .env.example .env
	@echo "Created .env — edit it with EvalHub, MLflow, judge, and guardian settings."

env-check: ## Verify .env exists
	@test -f .env || (echo "Missing .env — run: make env-init" && exit 1)

namespace: env-check ## Create or select the OpenShift project
	@oc get project "$(NAMESPACE)" >/dev/null 2>&1 || oc new-project "$(NAMESPACE)"
	@oc project "$(NAMESPACE)"

##@ Install (once)

install: env-check namespace ## Install EvalHub, Gaussia provider, and MLflow (default)
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set job.enabled=false \
		--set-string platform.provider.judge.model="$${GAUSSIA_JUDGE_MODEL}" \
		--set-string platform.provider.judge.modelProvider="$${GAUSSIA_JUDGE_MODEL_PROVIDER:-openai}" \
		--set-string platform.provider.judge.baseUrl="$${GAUSSIA_JUDGE_BASE_URL}" \
		--set-string platform.provider.judge.apiKey="$${GAUSSIA_JUDGE_API_KEY}" \
		--set-string platform.provider.judge.bosJsonClause="$${GAUSSIA_JUDGE_BOS_JSON_CLAUSE}" \
		--set-string platform.provider.judge.eosJsonClause="$${GAUSSIA_JUDGE_EOS_JSON_CLAUSE}" \
		--set-string platform.provider.judge.useStructuredOutput="$${GAUSSIA_JUDGE_USE_STRUCTURED_OUTPUT}" \
		--set-string platform.provider.guardian.model="$${GAUSSIA_GUARDIAN_MODEL}" \
		--set-string platform.provider.guardian.tokenizerModel="$${GAUSSIA_GUARDIAN_TOKENIZER_MODEL}" \
		--set-string platform.provider.guardian.baseUrl="$${GAUSSIA_GUARDIAN_BASE_URL}" \
		--set-string platform.provider.guardian.apiKey="$${GAUSSIA_GUARDIAN_API_KEY}" \
		--set-string platform.provider.guardian.chatCompletions="$${GAUSSIA_GUARDIAN_CHAT_COMPLETIONS}" \
		--set-string platform.provider.agentic.k="$${GAUSSIA_AGENTIC_K}" \
		--set-string platform.provider.agentic.threshold="$${GAUSSIA_AGENTIC_THRESHOLD}" \
		--set-string platform.provider.agentic.toolThreshold="$${GAUSSIA_AGENTIC_TOOL_THRESHOLD}")

install-no-mlflow: env-check namespace ## Install when namespace already has an MLflow CR named mlflow
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set job.enabled=false \
		--set platform.mlflow.create=false)

install-shared-mlflow: env-check namespace ## Install with MLflow service alias to another namespace
	@$(call with_env,helm upgrade --install "$(RELEASE)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set job.enabled=false \
		--set platform.mlflow.create=false \
		--set platform.mlflow.serviceAlias.enabled=true \
		--set platform.mlflow.serviceAlias.externalName="mlflow.$(MLFLOW_NAMESPACE).svc.cluster.local" \
		--set platform.mlflow.trackingUri="https://mlflow.$(MLFLOW_NAMESPACE).svc:8443" \
		--set platform.mlflow.workspace="$(NAMESPACE)" \
		--set platform.mlflow.rbacNamespace="$(NAMESPACE)")

wait-evalhub: ## Wait until the EvalHub deployment is ready
	@oc rollout status deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)"

upgrade-provider: env-check ## Apply judge/guardian settings from .env to the Helm release
	@$(call with_env,helm upgrade "$(RELEASE)" "$(CHART_DIR)" \
		--reuse-values \
		--namespace "$(NAMESPACE)" \
		--set job.enabled=false \
		--set mlflow.create=true \
		--set platform.mlflow.create=false \
		--set platform.mlflow.serviceAlias.enabled=true \
		--set platform.mlflow.serviceAlias.externalName="mlflow.$(MLFLOW_NAMESPACE).svc.cluster.local" \
		--set-string platform.mlflow.trackingUri="$${MLFLOW_TRACKING_URI:-https://mlflow.$(MLFLOW_NAMESPACE).svc:8443}" \
		--set platform.mlflow.workspace="$(NAMESPACE)" \
		--set platform.mlflow.rbacNamespace="$(NAMESPACE)" \
		--set-string platform.provider.judge.model="$${GAUSSIA_JUDGE_MODEL}" \
		--set-string platform.provider.judge.modelProvider="$${GAUSSIA_JUDGE_MODEL_PROVIDER:-openai}" \
		--set-string platform.provider.judge.baseUrl="$${GAUSSIA_JUDGE_BASE_URL}" \
		--set-string platform.provider.judge.apiKey="$${GAUSSIA_JUDGE_API_KEY}" \
		--set-string platform.provider.judge.bosJsonClause="$${GAUSSIA_JUDGE_BOS_JSON_CLAUSE}" \
		--set-string platform.provider.judge.eosJsonClause="$${GAUSSIA_JUDGE_EOS_JSON_CLAUSE}" \
		--set-string platform.provider.judge.useStructuredOutput="$${GAUSSIA_JUDGE_USE_STRUCTURED_OUTPUT}" \
		--set-string platform.provider.guardian.model="$${GAUSSIA_GUARDIAN_MODEL}" \
		--set-string platform.provider.guardian.tokenizerModel="$${GAUSSIA_GUARDIAN_TOKENIZER_MODEL}" \
		--set-string platform.provider.guardian.baseUrl="$${GAUSSIA_GUARDIAN_BASE_URL}" \
		--set-string platform.provider.guardian.apiKey="$${GAUSSIA_GUARDIAN_API_KEY}" \
		--set-string platform.provider.guardian.chatCompletions="$${GAUSSIA_GUARDIAN_CHAT_COMPLETIONS}" \
		--set-string platform.provider.agentic.k="$${GAUSSIA_AGENTIC_K}" \
		--set-string platform.provider.agentic.threshold="$${GAUSSIA_AGENTIC_THRESHOLD}" \
		--set-string platform.provider.agentic.toolThreshold="$${GAUSSIA_AGENTIC_TOOL_THRESHOLD}")
	@oc rollout restart deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)"
	@oc rollout status deploy/$(RELEASE)-evalhub -n "$(NAMESPACE)"

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
		--set evalhub.tenant="$(NAMESPACE)")
	@echo "Run release: $(RUN_NAME)"
	@echo "Follow logs: make logs RUN_NAME=$(RUN_NAME)"

run-all: env-check upgrade-provider wait-evalhub ## Submit all benchmarks (requires judge/guardian in .env)
	@$(call with_env,helm install "$(RUN_NAME)" "$(CHART_DIR)" \
		--namespace "$(NAMESPACE)" \
		--set platform.enabled=false \
		--set mlflow.create=false \
		--set quickstart.fixture="$(FIXTURE)" \
		--set quickstart.benchmarks=auto \
		--set quickstart.uniqueRun=true \
		--set evalhub.baseUrl="$(EVALHUB_SVC)" \
		--set evalhub.tenant="$(NAMESPACE)")
	@echo "Run release: $(RUN_NAME)"
	@echo "Follow logs: make logs RUN_NAME=$(RUN_NAME)"

install-external: env-check namespace ## Job-only install against existing EvalHub (uses EVALHUB_* from .env)
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
		--set evalhub.insecure=false)

run-local: env-check ## Submit a job from your workstation with uv (existing EvalHub)
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
	@test -n "$(RUN_NAME)" || (echo "Set RUN_NAME, e.g. make logs RUN_NAME=gaussia-evalhub-run-humanity-120000" && exit 1)
	@oc logs "job/$(RUN_NAME)-submit" -n "$(NAMESPACE)" -f

list-releases: ## List Helm releases in the namespace
	@helm list --namespace "$(NAMESPACE)"

uninstall-run: ## Remove a run release (set RUN_NAME)
	@test -n "$(RUN_NAME)" || (echo "Set RUN_NAME" && exit 1)
	@helm uninstall "$(RUN_NAME)" --namespace "$(NAMESPACE)"

uninstall: ## Remove the Helm release (EvalHub, provider, MLflow)
	@if helm status "$(RELEASE)" -n "$(NAMESPACE)" >/dev/null 2>&1; then \
		helm uninstall "$(RELEASE)" -n "$(NAMESPACE)"; \
	else \
		echo "Helm release $(RELEASE) not found in $(NAMESPACE) — nothing to uninstall"; \
	fi

cleanup-namespace: uninstall ## Delete the OpenShift project (destructive)
	@oc delete project "$(NAMESPACE)" --wait=false
