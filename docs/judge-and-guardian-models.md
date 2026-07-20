# Deploy judge and guardian models

The default `humanity` benchmark can run without external model endpoints. To run the full benchmark set, deploy a judge model and a guardian model in Red Hat OpenShift AI before installing this quickstart. The models named below are suggested examples, not hard requirements. You can use different models if they expose compatible endpoints and produce stable responses for the benchmark role.

| Model role | Used by | Deployment requirement |
| --- | --- | --- |
| Judge model | `context`, `conversational`, and `agentic` | OpenAI-compatible chat completions endpoint exposed at `/v1`. |
| Guardian model | `bias` | OpenAI-compatible chat completions endpoint exposed at `/v1`. |

We have tested with the following two models for both judge and guardian models:
- Qwen2.5-VL-7B-Instruct
- Qwen3.6-35B-A3B

Deploy the suggested judge model:

1. In OpenShift AI, search for the model in the model catalog.
2. Open the model detail page and select **Deploy model**.
3. Use model location `URI` with `oci://registry.redhat.io/rhai/modelcar-redhatai-qwen3-6-35b-a3b:3.0`.
4. Set model type to `Generative AI model (Example: LLM)`.
5. Review the deployment settings, deploy the model, and wait until the endpoint is ready.
6. Copy the model route, token, and served model name.

Deploy the suggested guardian model:

1. Download the model artifacts and upload them to S3-compatible object storage, such as MinIO.
2. In the OpenShift AI project, create an S3-compatible data connection that points to the bucket and path containing the guardian model.
3. Deploy a model from the existing data connection and set model type to `Generative AI model (Example: LLM)`.
4. Use a vLLM/KServe serving runtime with a GPU-capable hardware profile.
5. Enable the external route and token authentication.
6. Wait until the endpoint is ready, then copy the model route, token, and served model name.

Copy the  `.env.example` to `.env` and ensure that `GAUSSIA_JUDGE_API_KEY` and `GAUSSIA_GUARDIAN_API_KEY` are set.

```bash
make env-init
```

`GAUSSIA_JUDGE_API_KEY` and `GAUSSIA_GUARDIAN_API_KEY` are set in `.env`. `make install` / `make upgrade-provider` apply them into an OpenShift Secret for the UI, and into the provider ConfigMap for EvalHub Jobs (EvalHub drops `valueFrom` on provider env). To bring your own Secret for the UI, set `platform.provider.existingSecret`.

Set `GAUSSIA_JUDGE_MODEL_PROVIDER` to the LangChain provider that matches your judge endpoint. Use `openai` for OpenShift AI or LiteLLM routes that expose an OpenAI-compatible `/v1` API. Custom served model names such as `llama-scout-17b` require this setting because LangChain cannot infer the provider from the model name alone.

Keep `GAUSSIA_GUARDIAN_CHAT_COMPLETIONS="true"` when the guardian uses Groq or another OpenAI-compatible chat endpoint. Setting it to `false` selects the legacy `/completions` endpoint, which Groq does not expose for chat models.

If you already have compatible judge and guardian endpoints, use those values instead.