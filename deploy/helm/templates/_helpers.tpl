{{- define "gaussia-evalhub.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "gaussia-evalhub.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := include "gaussia-evalhub.name" . -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "gaussia-evalhub.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.platformServiceAccountName" -}}
{{- default (printf "%s-platform" (include "gaussia-evalhub.fullname" .)) .Values.platform.serviceAccountName -}}
{{- end -}}

{{- define "gaussia-evalhub.evalhubName" -}}
{{- default (printf "%s-evalhub" (include "gaussia-evalhub.fullname" .)) .Values.platform.evalhub.name -}}
{{- end -}}

{{- define "gaussia-evalhub.mlflowName" -}}
{{- default "mlflow" .Values.platform.mlflow.name -}}
{{- end -}}

{{- define "gaussia-evalhub.mlflowWorkspace" -}}
{{- default .Release.Namespace .Values.platform.mlflow.workspace -}}
{{- end -}}

{{- define "gaussia-evalhub.mlflowRbacNamespace" -}}
{{- default (include "gaussia-evalhub.mlflowWorkspace" .) .Values.platform.mlflow.rbacNamespace -}}
{{- end -}}

{{- define "gaussia-evalhub.mlflowTrackingUri" -}}
{{- default (printf "https://%s.%s.svc:8443" (include "gaussia-evalhub.mlflowName" .) .Release.Namespace) .Values.platform.mlflow.trackingUri -}}
{{- end -}}

{{- define "gaussia-evalhub.mlflowServiceAliasExternalName" -}}
{{- default (printf "%s.%s.svc.cluster.local" (include "gaussia-evalhub.mlflowName" .) (include "gaussia-evalhub.mlflowRbacNamespace" .)) .Values.platform.mlflow.serviceAlias.externalName -}}
{{- end -}}

{{- define "gaussia-evalhub.providerImage" -}}
{{- if .Values.platform.provider.image.fullReference -}}
{{- .Values.platform.provider.image.fullReference -}}
{{- else -}}
{{- printf "%s:%s" .Values.platform.provider.image.repository .Values.platform.provider.image.tag -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.evalhubBaseUrl" -}}
{{- if .Values.evalhub.baseUrl -}}
{{- .Values.evalhub.baseUrl -}}
{{- else if and .Values.platform.enabled .Values.platform.evalhub.enabled -}}
{{- printf "http://%s:8080" (include "gaussia-evalhub.evalhubName" .) -}}
{{- else -}}
{{- "http://evalhub.example.com" -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.evalhubTenant" -}}
{{- default .Release.Namespace .Values.evalhub.tenant -}}
{{- end -}}

{{- define "gaussia-evalhub.waitForMlflow" -}}
{{- if ne (toString .Values.quickstart.waitForMlflow) "" -}}
{{- .Values.quickstart.waitForMlflow -}}
{{- else -}}
{{- and .Values.platform.enabled .Values.platform.mlflow.enabled -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.labels" -}}
app.kubernetes.io/name: {{ include "gaussia-evalhub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "gaussia-evalhub.providersChecksum" -}}
{{- printf "%s" .Values.platform.provider | toYaml | sha256sum -}}
{{- end -}}

{{- define "gaussia-evalhub.uiName" -}}
{{- default "gaussia-ui" .Values.ui.name -}}
{{- end -}}

{{- define "gaussia-evalhub.uiServiceAccountName" -}}
{{- default "ocp-api-edit" .Values.ui.serviceAccount.name -}}
{{- end -}}

{{- define "gaussia-evalhub.uiEnvConfigMapName" -}}
{{- if .Values.ui.existingEnvConfigMap -}}
{{- .Values.ui.existingEnvConfigMap -}}
{{- else -}}
{{- default (printf "%s-env" (include "gaussia-evalhub.uiName" .)) .Values.ui.envConfigMap -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.uiImage" -}}
{{- printf "%s:%s" .Values.ui.image.repository (.Values.ui.image.tag | default .Chart.AppVersion) -}}
{{- end -}}

{{- define "gaussia-evalhub.uiLabels" -}}
app: {{ include "gaussia-evalhub.uiName" . }}
app.kubernetes.io/component: {{ include "gaussia-evalhub.uiName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}


{{- define "gaussia-evalhub.providerSecretName" -}}
{{- if .Values.platform.provider.existingSecret -}}
{{- .Values.platform.provider.existingSecret -}}
{{- else -}}
{{- printf "%s-provider" (include "gaussia-evalhub.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.providerSecretEnabled" -}}
{{- if or .Values.platform.provider.existingSecret .Values.platform.provider.judge.apiKey .Values.platform.provider.guardian.apiKey -}}
true
{{- end -}}
{{- end -}}

{{/*
EvalHub provider Jobs only honor env.name/value (valueFrom is dropped).
Prefer Helm values; when using existingSecret with empty values, look up the Secret.
*/}}
{{- define "gaussia-evalhub.judgeApiKey" -}}
{{- if .Values.platform.provider.judge.apiKey -}}
{{- .Values.platform.provider.judge.apiKey -}}
{{- else if .Values.platform.provider.existingSecret -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace .Values.platform.provider.existingSecret -}}
{{- if $secret -}}
{{- index $secret.data (.Values.platform.provider.judgeApiKeyKey | default "GAUSSIA_JUDGE_API_KEY") | b64dec -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.guardianApiKey" -}}
{{- if .Values.platform.provider.guardian.apiKey -}}
{{- .Values.platform.provider.guardian.apiKey -}}
{{- else if .Values.platform.provider.existingSecret -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace .Values.platform.provider.existingSecret -}}
{{- if $secret -}}
{{- index $secret.data (.Values.platform.provider.guardianApiKeyKey | default "GAUSSIA_GUARDIAN_API_KEY") | b64dec -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "gaussia-evalhub.providerEntrypoint" -}}
export GAUSSIA_JUDGE_MODEL='{{ .Values.platform.provider.judge.model | replace `'` `'\''` }}'
export GAUSSIA_JUDGE_MODEL_PROVIDER='{{ .Values.platform.provider.judge.modelProvider | replace `'` `'\''` }}'
export GAUSSIA_JUDGE_BASE_URL='{{ .Values.platform.provider.judge.baseUrl | replace `'` `'\''` }}'
export GAUSSIA_JUDGE_BOS_JSON_CLAUSE='{{ .Values.platform.provider.judge.bosJsonClause | replace `'` `'\''` }}'
export GAUSSIA_JUDGE_EOS_JSON_CLAUSE='{{ .Values.platform.provider.judge.eosJsonClause | replace `'` `'\''` }}'
export GAUSSIA_GUARDIAN_MODEL='{{ .Values.platform.provider.guardian.model | replace `'` `'\''` }}'
export GAUSSIA_GUARDIAN_TOKENIZER_MODEL='{{ .Values.platform.provider.guardian.tokenizerModel | replace `'` `'\''` }}'
export GAUSSIA_GUARDIAN_BASE_URL='{{ .Values.platform.provider.guardian.baseUrl | replace `'` `'\''` }}'
export GAUSSIA_GUARDIAN_CHAT_COMPLETIONS='{{ .Values.platform.provider.guardian.chatCompletions | replace `'` `'\''` }}'
export GAUSSIA_PROVIDER_PACKAGE_SPEC='{{ .Values.platform.provider.packageSpec | replace `'` `'\''` }}'
GAUSSIA_PACKAGE_SPEC="${GAUSSIA_PACKAGE_SPEC:-${GAUSSIA_PROVIDER_PACKAGE_SPEC}}"
if [ -n "${GAUSSIA_PACKAGE_SPEC}${EVALHUB_SDK_SPEC}" ]; then
  python -m pip install --no-cache-dir ${GAUSSIA_PACKAGE_SPEC} ${EVALHUB_SDK_SPEC}
fi
python -m gaussia.integrations.evalhub.adapter
{{- end -}}
