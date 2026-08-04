# AGENTS.md - nopaque Python SDK

Instructions for AI coding agents working **on this repository**.

If you are instead trying to *call* the Nopaque API from some other project, read <https://www.nopaque.co.uk/AGENTS.md> - it covers authentication, endpoints, and the cost-and-consent rules for operations that place real phone calls. Do not duplicate that content here.

## What this is

`nopaque` is the official Python client for the [Nopaque](https://www.nopaque.co.uk) REST API, which drives TotalPath - a voice testing platform that maps, tests and load-tests IVRs and AI voice agents over real PSTN calls.

- Published package: <https://pypi.org/project/nopaque/>
- API reference: <https://www.nopaque.co.uk/docs>
- OpenAPI 3.1 document: <https://api.nopaque.co.uk/openapi.json>

## This SDK is hand-written, not generated

There is no code generator in this repository and no generated-code markers in `src/`. Edit the source directly.

When the API adds an endpoint, the change is usually three files: a model in `src/nopaque/models/`, a resource method in `src/nopaque/resources/`, and a test in `tests/resources/`. Check the OpenAPI document above for the actual request and response shapes rather than inferring them.

## Layout

| Path | Contents |
| --- | --- |
| `src/nopaque/` | Package root. `_client.py` is the entry point; leading-underscore modules are internal plumbing (transport, retry, pagination, polling, config, errors, S3). |
| `src/nopaque/models/` | Pydantic v2 request/response models, one module per API domain. |
| `src/nopaque/resources/` | Resource classes exposing the methods users call, one module per API domain. |
| `tests/` | Unit tests. `tests/resources/` mirrors `src/nopaque/resources/`. |
| `tests/integration/` | Live tests against the dev API. Excluded from the default run. |
| `examples/` | Runnable usage examples, sync and async. |

## Commands

This project uses [hatch](https://hatch.pypa.io/). Every command below is the one CI actually runs (`.github/workflows/ci.yml`).

```bash
pip install hatch build     # one-time setup

hatch run lint              # ruff check src/nopaque tests
hatch run type              # mypy src/nopaque
hatch run test              # pytest tests  (integration tests excluded)
hatch run format            # ruff format src/nopaque tests
python -m build             # build distributions
```

CI runs `lint`, `type`, `test` and `build` on Python 3.9, 3.10, 3.11 and 3.12. **Run at least `hatch run lint && hatch run type && hatch run test` before opening a PR.**

### Integration tests place real API calls

```bash
hatch run test:integration
```

These hit the live dev API and require `NOPAQUE_API_KEY` (and optionally `NOPAQUE_BASE_URL`). They are excluded from the default `pytest` run by `addopts = "--ignore=tests/integration"` and are normally exercised only by the nightly workflow. **Do not run them casually** - some API operations place real outbound phone calls and bill a workspace.

## Conventions that will trip you up

- **Target Python 3.9.** `requires-python = ">=3.9"`, and `ruff` is configured with `target-version = "py39"`. PEP 585/604 generics (`list[str]`, `X | None`) are deliberately not used because runtime-evaluated Pydantic models need 3.10+ for that syntax - `UP006`, `UP007`, `UP035` and `UP045` are in the ruff ignore list for exactly this reason. Do not "modernise" them back in.
- **Line length is 100** (`[tool.ruff] line-length = 100`).
- **Async mode is automatic** (`asyncio_mode = "auto"`), so async tests need no explicit marker.
- **Config resolution order** is documented in `src/nopaque/_config.py`: explicit `api_key=` argument first, then the `NOPAQUE_API_KEY` environment variable. `NOPAQUE_BASE_URL` overrides the default base URL.
- **Version lives in `src/nopaque/_version.py`** and is read dynamically by hatch. Do not hardcode it elsewhere.

## Contributing

Branch from `main`, open a PR against `main`. CI must be green.
