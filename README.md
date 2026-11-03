# Scaleway Generative APIs provider for Hermes

Use [Scaleway Generative APIs](https://www.scaleway.com/en/generative-apis/) models in
[Hermes Agent](https://github.com/NousResearch/hermes-agent) as a first-class provider: pick
**Scaleway** in `hermes model`, or run `hermes chat --provider scaleway` (alias `scw`).

Hosted by the Scaleway organization; not affiliated with NousResearch.

## Why a plugin?

Scaleway's API is OpenAI-compatible, so Hermes can reach it without one — a hand-written
`providers:` custom block with the base URL and `SCW_SECRET_KEY`. What that loses:

| | Without the plugin (custom provider) | With it |
|---|---|---|
| Choosing Scaleway | A manual `config.yaml` block, every field spelled out | `--provider scaleway` (alias `scw`), a prompted row in `hermes model` |
| Context window | The generic 256K default — `llama-3.3-70b-instruct` really has 100K and `mistral-small-3.2-24b-instruct-2506` 128K, so compression runs too late | The real windows, 100K to 262K, from [models.dev](https://models.dev) |
| Pricing, reasoning/tool-call badges | None (a further hand-written `catalog_provider` would be needed) | Per-model, from models.dev |
| Model picker | The raw `/v1/models` catalog, embeddings and transcription models included | The live catalog, with this curated tool-calling list standing in when the probe fails — `gpt-oss-120b` deliberately excluded: Scaleway serves its tool-calling on the beta Responses API only |
| Auxiliary tasks (compression, summaries) | The main (large) model | A cheap auxiliary tier: `mistral-small-3.2-24b-instruct-2506`, the cheapest tool-calling vision-capable model (title generation may lead with a fast-tier pick such as `deepseek-v4.1-flash-1017`) |

## Install

Once admitted to the Hermes plugin catalog (the catalog pins the reviewed commit):

```sh
hermes plugins install scaleway-provider
```

Or straight from this repository at a reviewed commit — the plugin lives in the
`scaleway-provider/` subdirectory, and `<full-commit-sha>` is the 40-character SHA you reviewed:

```sh
hermes plugins install "https://github.com/scaleway/hermes-scaleway-provider#scaleway-provider" --ref <full-commit-sha>
```

## Configure

The credential is the **secret key** of a Scaleway IAM API key (create one at
[console.scaleway.com/iam/api-keys](https://console.scaleway.com/iam/api-keys); the IAM
principal needs the `GenerativeApisModelAccess` permission set). It is the same
`SCW_SECRET_KEY` the Scaleway CLI and SDKs use, so an existing CLI setup works as-is:

```sh
hermes config set SCW_SECRET_KEY <your-secret-key>
```

Because `SCW_SECRET_KEY` is ambient (exported by the Scaleway CLI for other purposes), Hermes
never auto-detects this provider from it: select Scaleway explicitly with `--provider scaleway`
(alias `scw`), `hermes model`, or `model.provider: scaleway` in config.yaml. An optional
`SCALEWAY_BASE_URL` overrides the default `https://api.scaleway.ai/v1`.

## Models

The setup default is `deepseek-v4.1-flash-1017`. Model metadata (context windows, pricing,
reasoning/tool-call badges) resolves through Hermes' [models.dev](https://models.dev)
integration at runtime; the table below is the recorded 2026-11-03 snapshot of the curated
fallback list:

| Model | Context | Vision | Reasoning |
|---|---|---|---|
| `deepseek-v4.1-flash-1017` | 256K | ✓ | ✓ |
| `glm-5.3` | 256K | | ✓ |
| `glm-5.2` | 256K | | ✓ |
| `qwen3.5-397b-a17b` | 256K | ✓ | ✓ |
| `qwen3.8-27b` | 262K | ✓ | ✓ |
| `qwen3.6-35b-a3b` | 128K | ✓ | ✓ |
| `mistral-medium-3.5-128b` | 256K | ✓ | ✓ |
| `mistral-small-3.2-24b-instruct-2506` | 128K | ✓ | |
| `gemma-4-26b-a4b-it` | 256K | ✓ | ✓ |
| `llama-3.3-70b-instruct` | 100K | | |
| `qwen3-235b-a22b-instruct-2507` | 260K | | |

## Security and footprint

- Registers one model provider, `scaleway`, when Hermes loads it. No tools, hooks, commands or
  background threads.
- Network: chat requests and a `GET /v1/models` catalog probe go to
  `https://api.scaleway.ai/v1` (or `SCALEWAY_BASE_URL`) through Hermes' own client, carrying
  `SCW_SECRET_KEY`. The plugin itself opens no connections.
- Reads no files, writes no files, starts no processes and has no dependencies beyond Hermes.
  Hermes, not the plugin, reads the two variables, per profile.

## Compatibility

Hermes 0.22.6 or newer. The profile uses the `models_dev_id` and `ambient_credentials` plugin
fields, added to Hermes on 2026-10-25 and first released in v0.22.6; earlier releases (up to
0.22.5) do not carry them, so the plugin's `requires_hermes` guard holds it back there instead
of failing silently. CI runs the tests against Hermes `main` and the minimum release `v0.22.6`
every day.

## Changelog

### 1.1.0

- Plugin directory layout (`scaleway-provider/`): the installed payload is exactly the plugin;
  tests, fixtures and CI live around it.
- `requires_hermes: ">=0.22.6"` (v0.22.6 is the first release carrying the profile fields) and
  `optional_env: [SCALEWAY_BASE_URL]` in the manifest.
- Offline unit tests with a stub `providers` package; a recorded models.dev snapshot guarding
  the curated list; end-to-end tests against a real Hermes home using Hermes' own loopback LLM
  (nothing talks to Scaleway); packaging tests.
- CI: a 3-OS × 2-Python offline matrix, Hermes `main` end-to-end plus `hermes plugins validate`,
  and a daily cron.

### 1.0.0

- The `scaleway` model provider (alias `scw`): curated tool-calling list led by
  `deepseek-v4.1-flash-1017`, models.dev metadata, ambient `SCW_SECRET_KEY`, and the cheapest
  vision-capable aux model.

## License

MIT — see [the license file](https://github.com/scaleway/hermes-scaleway-provider/blob/main/LICENSE).
