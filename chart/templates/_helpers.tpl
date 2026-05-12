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
