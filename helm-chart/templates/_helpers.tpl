{{/*
Expand the name of the chart.
*/}}
{{- define "taipei-city-dashboard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "taipei-city-dashboard.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "taipei-city-dashboard.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "taipei-city-dashboard.labels" -}}
helm.sh/chart: {{ include "taipei-city-dashboard.chart" . }}
{{ include "taipei-city-dashboard.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "taipei-city-dashboard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "taipei-city-dashboard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "taipei-city-dashboard.frontend.labels" -}}
{{ include "taipei-city-dashboard.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "taipei-city-dashboard.frontend.selectorLabels" -}}
{{ include "taipei-city-dashboard.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Backend labels
*/}}
{{- define "taipei-city-dashboard.backend.labels" -}}
{{ include "taipei-city-dashboard.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "taipei-city-dashboard.backend.selectorLabels" -}}
{{ include "taipei-city-dashboard.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "taipei-city-dashboard.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "taipei-city-dashboard.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create image name
*/}}
{{- define "taipei-city-dashboard.image" -}}
{{- $repositoryName := .repository -}}
{{- /* Only use provided .tag; fail if empty to avoid pulling non-existent fallback images */ -}}
{{- $explicitTag := .tag | toString -}}
{{- if eq $explicitTag "" }}
{{- fail (printf "Image tag must be explicitly set for repository %s - no fallback allowed" $repositoryName) }}
{{- end }}
{{- printf "%s:%s" $repositoryName $explicitTag -}}
{{- end }}


