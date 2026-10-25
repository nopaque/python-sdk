# nopaque - Python SDK for Nopaque

Official Python client for the [Nopaque](https://nopaque.co.uk) API.

## Install

```bash
pip install nopaque
```

## Quick start

```python
from nopaque import Nopaque
from nopaque.models.mapping import MappingJobConfig

client = Nopaque(api_key="nop_live_...")   # or set NOPAQUE_API_KEY

# Create a mapping job and wait for it to complete
job = client.mapping.create(
    name="Main IVR",
    phone_number="+441234567890",
    config=MappingJobConfig(mapping_mode="dtmf"),
)
client.mapping.start(job.id)
final = client.mapping.wait_for_complete(job.id)
print(final.status)

# List audio files with automatic pagination
for audio in client.audio.list():
    print(audio.id, audio.file_name)

client.close()
```

## Async

```python
import asyncio
from nopaque import AsyncNopaque

async def main():
    async with AsyncNopaque() as client:
        job = await client.mapping.get("map_abc123")
        print(job.status)

asyncio.run(main())
```

## Digital testing (beta)

Run automated chat-channel conversations against a bot and get a pass/fail
verdict. Access is limited to beta workspaces during the beta period.

`sector` and `mission` are required — the API returns a 400 without them.

```python
run = client.digital_testing.create(
    target_ref="acme/billing-bot",
    target={"transport": "web-widget", "url": "https://example.com/support"},
    sector="utilities",
    mission="check the outstanding balance",
    kind="freeform",
    acceptance="The bot states the outstanding balance.",
)

finished = client.digital_testing.wait_for_run(run.id)
# `completed` with outcome "fail" is a RESULT, not an error.
print(finished.status, finished.outcome, finished.pass_rate)
```

Reusable configs live under `client.digital_test_configs`
(`create`, `list`, `get`, `update`, `delete`, `launch`), and
`client.digital_compliance` lists compliance audits and fetches a per-target
report.

## Survey tests

A survey test runs the other way round from a call test: your survey platform
starts the conversation, and a nopaque respondent answers it. Starting a test
claims one of your workspace's survey numbers; you then send your survey to it.

```python
run = client.surveys.start(
    config_id="d41eaa86-34ae-4b7c-b5cc-debf7c254b44",
    sender="+447921721840",   # the number your survey platform sends FROM
    window_secs=600,          # the survey must arrive within this window
)
print("Send the survey to", run.agent_e164)

# ... trigger your survey platform, aimed at run.agent_e164 ...

result = client.surveys.wait_for_result(run.run_id)   # until the transcript is final
print(result.outcome, result.answers_given)
for turn in result.turns:
    print(turn.at, turn.from_, turn.text)
```

`start` raises `ConflictError` when the workspace has no free survey number for
that sender. `wait_for_result` returns a failed capture rather than raising it;
check `result.capture.status`. Saved respondents live under
`client.surveys.configs` (`create`, `list`, `get`, `update`, `delete`), and past
results under `client.surveys.results` (`list`, `list_page`, `get`).

## Voices

List the operator-enabled voices a mission test may use, and which one is the
default.

```python
voices = client.testing.list_voices()
for voice in voices.voices:
    print(voice.voice_id, voice.name)
print("default:", voices.default_voice_id)
```

## Test configs

`client.testing.configs` holds reusable scripted test plans. `create()` takes
`name`, `phone_number` and `steps`, plus optional `description`, `type`
(`"standard"` or `"parameterized"`), `profile_id`, `required_parameters`,
`schedule_id`, `max_duration_secs` (30-1800, whole-call ceiling; the tester
defaults to 300) and `carrier_route_id`. Only the arguments you pass are sent.

```python
config = client.testing.configs.create(
    name="Transfer to agent",
    phone_number="+442012345678",
    max_duration_secs=900,
    steps=[
        {"name": "Main menu", "type": "dtmf", "expected": "Press 1 for sales", "dtmf": "1"},
        {"name": "Hold music", "type": "hold", "durationSecs": 600},
    ],
)

# update() changes only what you pass. schedule_id, max_duration_secs and
# carrier_route_id can also be cleared with None; omit them to leave them as is.
client.testing.configs.update(config.id, description="Nightly", max_duration_secs=None)
```

## Bring your own carrier

Invite-only. A workspace can dial its tests through its own SIP trunk (a
*carrier integration*, set up with nopaque) instead of nopaque's network. Each
trunk has *routes* that pick a vendor by tech prefix and optional `X-` headers.
Put a route's `route_id` on a test config as `carrier_route_id`, and that
config's calls go out through the route. If the route can't be dialled when a
run starts, the run is refused (`ConflictError`); the number is never called
normally instead.

```python
from nopaque import Nopaque

client = Nopaque()

# Trunks are read-only here; each one lists its routes.
for trunk in client.testing.carrier_integrations.list():
    print(trunk.integration_id, trunk.name, trunk.status, len(trunk.routes))
trunk = client.testing.carrier_integrations.list()[0]

route = client.testing.carrier_integrations.routes.create(
    trunk.integration_id,
    name="Vendor X premium",
    tech_prefix="R7Q2#",  # dialled in front of the number
)
print(route.route_id, route.dialable)

config = client.testing.configs.create(
    name="Main menu via own trunk",
    phone_number="+442012345678",
    steps=[{"name": "Main menu", "type": "dtmf", "expected": "Press 1 for sales", "dtmf": "1"}],
    carrier_route_id=route.route_id,
)

run = client.testing.runs.create(test_config_id=config.id)  # dials config.phone_number
final = client.testing.runs.wait_for_run(run.id)

print(final.outcome, final.carrier)  # carrier: integration_id / route_id dialled
if final.call_telemetry and final.call_telemetry.telephony:
    print("SIP hang-up cause:", final.call_telemetry.telephony.get("sipHangupCause"))
for step in final.step_results:
    print(step.action_type, step.action_value, step.outcome, step.similarity)
    print("  heard:", step.actual_transcript)
```

Also available: `carrier_integrations.get(integration_id)`,
`carrier_integrations.routes.list(integration_id)`,
`routes.get(integration_id, route_id)` and
`routes.update(integration_id, route_id, name=..., tech_prefix=..., custom_headers=..., enabled=...)`.
`enabled=False` turns a route off. `configs.update(config_id, carrier_route_id=None)`
removes the route from a config, and the number is dialled normally again.

## Features

- Full coverage of the Nopaque REST API via API-key auth
- Typed Pydantic v2 models for every request and response
- Paired sync (`Nopaque`) and async (`AsyncNopaque`) clients
- Automatic pagination for list endpoints
- Polling helpers for long-running jobs (`wait_for_complete`)
- One-call audio upload/download wrapping the presigned-URL flow
- Method-aware retry with exponential jitter and `Retry-After` honor
- Typed exception hierarchy (`NotFoundError`, `RateLimitError`, etc.)

## Documentation

Full reference: <https://nopaque.co.uk/docs/sdks>

## Authentication

Pass your API key to the client:

```python
Nopaque(api_key="nop_live_...")
```

Or set the environment variable:

```bash
export NOPAQUE_API_KEY=nop_live_...
```

API keys are workspace-scoped and subject to per-minute rate limits based on
your subscription tier. Free tier cannot use API keys.

## Requirements

- Python 3.9+
- `httpx >= 0.27`, `pydantic >= 2.6`

## License

MIT
