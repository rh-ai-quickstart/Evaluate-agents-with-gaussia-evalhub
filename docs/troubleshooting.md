# Troubleshooting

## EvalHub returns `400 Bad Request` when submitting a job

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

## MLflow connectivity fails

If MLflow connectivity fails on the shared-MLflow path, confirm the alias service exists:

```bash
oc get svc mlflow -n "${NAMESPACE:-gaussia-evalhub-quickstart}"
```

To locate shared MLflow in your cluster (no Make equivalent):

```bash
oc get svc -A | grep -i mlflow
oc get mlflow -A
```
