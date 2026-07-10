# Gaussia metric families

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

[Gaussia]: https://github.com/gaussia-labs/pygaussia
