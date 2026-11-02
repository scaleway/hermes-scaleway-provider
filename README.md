# hermes-scaleway-provider

[Scaleway Generative APIs](https://www.scaleway.com/en/docs/ai-ml/generative-apis/) as a
[Hermes Agent](https://github.com/NousResearch/hermes-agent) model provider — European,
OpenAI-compatible, pay-per-use (GLM, Qwen, DeepSeek, Mistral, Gemma, Llama...).

This is a standalone Hermes plugin, not affiliated with NousResearch.

## Install

Once admitted to the Hermes plugin catalog:

```bash
hermes plugins install scaleway-provider
```

Or install straight from this repository at a reviewed commit (replace the SHA with the one
you reviewed):

```bash
hermes plugins install https://github.com/reda-maizate/hermes-scaleway-provider
```

## Configure

The credential is the **secret key** of a Scaleway IAM API key (create one at
[console.scaleway.com/iam/api-keys](https://console.scaleway.com/iam/api-keys); the IAM
principal needs the `GenerativeApisModelAccess` permission set). It is the same
`SCW_SECRET_KEY` the Scaleway CLI and SDKs use, so an existing CLI setup works as-is:

```bash
hermes config set SCW_SECRET_KEY <your-secret-key>
```

Because `SCW_SECRET_KEY` is ambient (exported by the Scaleway CLI for other purposes),
Hermes never auto-detects this provider from it: select Scaleway explicitly with
`--provider scaleway` (alias `scw`), `hermes model`, or `model.provider: scaleway` in
config.yaml. An optional `SCALEWAY_BASE_URL` overrides the default
`https://api.scaleway.ai/v1`.

## Models

The default is `deepseek-v4.1-flash-1017`; the model picker shows the live `/v1/models`
catalog merged with a curated, tool-calling fallback list (serverless models that drive an
agent over the chat-completions wire). Auxiliary tasks (session titles, compression) run
on `mistral-small-3.2-24b-instruct-2506`, the cheapest vision-capable tier. `gpt-oss-120b`
is deliberately not curated: Scaleway serves its tool-calling on the beta Responses API
only, which cannot drive an agent over chat-completions.

Model metadata (context windows, pricing, reasoning/tool-call badges) resolves through
Hermes' models.dev integration.

## Development

The tests exercise the plugin through Hermes' real user-plugin discovery path and need a
Hermes source checkout next to this repository (override with `HERMES_SOURCE`):

```bash
HERMES_SOURCE=/path/to/hermes-agent /path/to/hermes-agent/.venv/bin/python -m pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).
