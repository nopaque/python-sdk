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

Saved connection definitions are on `client.digital_testing` too:
`create_connector`, `list_connectors`, `list_connectors_page`, `get_connector`,
`update_connector` and `delete_connector`.
`client.digital_testing.list_connector_types()` returns each connector type
with the form fields its `config` takes. A connector's `type` and `target_ref`
cannot be changed after creation, and deleting one that a saved config still
uses raises `ConflictError`.

```python
connector = client.digital_testing.create_connector(
    name="Billing bot",
    type="http-json",
    target_ref="acme/billing-bot",
    config={"url": "https://bot.example.com/chat"},
)
```

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

# A short-lived link to hear one, when the voice has a sample.
if voices.voices[0].has_sample:
    print(client.testing.get_voice_sample(voices.voices[0].voice_id).url)
```

### Generating speech

`client.audio.generate()` speaks text in one of those voices and stores the
result as an MP3 voice clip in your workspace. **It is billed** per character
of `text`, on every call, including repeats. It places no phone call.

```python
clip = client.audio.generate(
    voice_id=voices.default_voice_id,
    text="I'd like to check my balance, please.",
    settings={"speed": 0.9},   # Ultra voices only: speed, volume, emotion
)
print(clip.audio_id, clip.characters)
```

## Test configs

`client.testing.configs` holds reusable scripted test plans. `create()` takes
`name`, `phone_number` and `steps`, plus optional `description`, `type`
(`"standard"` or `"parameterized"`), `profile_id`, `required_parameters`,
`schedule_id`, `max_duration_secs` (30-1800, whole-call ceiling; the tester
defaults to 300), `carrier_route_id` and `language`. Only the arguments you
pass are sent.

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

### Languages

Two different sets, and mixing them up is a 400. Both are exported as
`Literal` aliases, so a typo is a type error rather than a failed run.

`TranscriptionLanguage` is the language audio is **transcribed** in. It applies
to standard test configs (`language=`) and to mapping jobs
(`MappingJobConfig(language=...)`), and defaults to `en-GB` when omitted.
English needs its region here - `en-GB`, `en-US`, `en-AU`, `en-IN`, `en-NZ`.

`CallLanguage` is the language a **mission-test call** is held in
(`client.mission_tests.create(language=...)`). Absent means English. Use
`"multi"` when the IVR may start in English and switch.

```python
from nopaque import CallLanguage, TranscriptionLanguage

# Transcription: a region is required for English.
client.testing.configs.create(
    name="Spanish main menu", phone_number="+34910000000", steps=[], language="es"
)

# Mission-test call language: bare "en" is valid HERE and only here.
client.mission_tests.create(
    sector="insurance",
    mission="Buy a policy",
    acceptance="Bot offers a quote",
    profile={"phone_number": "+34910000000"},
    language="es",
)
```

`client.testing.list_languages()` returns both sets with their labels and
defaults (`GET /languages`), for showing a person a picker:

```python
langs = client.testing.list_languages()
print([lang.code for lang in langs.transcription.languages], langs.call.default)
```

The trap: bare `en` is a valid **call** language but is rejected as a
transcription language, which wants `en-GB`. Every other call language
(`multi`, `es`, `fr`, `de`, `it`, `pt`, `nl`, `hi`, `ru`, `ja`) appears in both
sets, which is what makes it easy to miss. Omitting `language` on an update
leaves the saved value untouched.

The aliases are **strict on write, lenient on read**. The `language=`
parameters you pass to `configs.create()`, `configs.update()` and
`mission_tests.create()` are typed to the `Literal`, so a typo is caught
before a request goes out. The matching fields on the models you read back
(`TestConfig.language`, `MissionTestRun.language`,
`MappingJobConfig.language`) are plain `str`, so a row saved with a code this
SDK version has never heard of still parses instead of raising. Both aliases
are exported either way, for annotating your own variables:

```python
from nopaque import TranscriptionLanguage

preferred: TranscriptionLanguage = "en-GB"
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

## Checking a destination

`client.testing.check_destination()` says whether a test, mission test or map
to a number would be dialled, and why not if it would not. Nothing is saved or
dialled.

```python
check = client.testing.check_destination(phone_number="+6493000000")
if not check.allowed:
    print(check.message)   # a sentence to show the person
```

## Re-running failed batch tests

`client.batches.rerun(batch_run_id)` starts a new batch run of only the failed
tests from an earlier one. **It places real calls.** Pass `filter="errors"` or
`"mismatches"` to narrow it, or `members=[...]` to pick tests.

```python
child = client.batches.rerun(batch_run.id, filter="errors")
client.batches.wait_for_run(child.id)
```

## Mission test analyses

`client.mission_tests.get_analyses(run_id)` returns the post-call analyses of a
mission test run, the newest of each type. A type that has not run yet is
`None`.

```python
analyses = client.mission_tests.get_analyses(run.id).analyses
if analyses.judge_mission and analyses.judge_mission.status == "completed":
    print(analyses.judge_mission.data)
```

## Load-test reports, exports and failure patterns

These are on `client.load_testing`. Each takes a load-test **run** id, not the
load-test config id (reports take a list of them).

```python
lt = client.load_testing

# Why calls failed, grouped into patterns, and the calls in one pattern.
patterns = lt.get_failure_patterns(run_id)
for p in patterns.patterns:
    print(p.id, p.label, p.owner, p.count)
for call in lt.list_failure_pattern_calls(run_id, patterns.patterns[0].id):
    print(call.call_id, call.failed_step_name)
lt.reclassify_failure_patterns(run_id)   # rerun the rules in the background

# A zip of every call and step in one run.
export = lt.create_export(run_id)
export = lt.get_export(run_id, export.export_id)   # poll until status == "ready"
print(export.download_url)

# A report (data zip, Excel workbook, PDF) over up to 20 finished runs.
report = lt.create_report(load_test_run_ids=[run_id], packs=["pdf"])
report = lt.get_report(report.report_id)           # poll until status == "ready"
print(lt.get_report_file_url(report.report_id, "pdf").url)
```

Also available: `list_reports`, `list_reports_page`, `delete_report`,
`list_exports` and `list_failure_pattern_calls_page`.

## Numbers

The phone numbers your workspace rents: caller IDs for tests, and numbers your
systems dial or text back. **Ordering a number spends money**: it carries a
monthly charge, and repeating an order buys a second number.

```python
held = client.numbers.list()
print(len(held.numbers), held.allowance.remaining if held.allowance else None)

found = client.numbers.list_available(country="GB", number_type="outbound")
choice = found.numbers[0]

order = client.numbers.order(e164=choice.e164, number_type="outbound", country="GB")
if order.order_id:                       # not live yet; UK mobiles take about a day
    print(client.numbers.get_order(order.order_id).progress.waiting_on)

client.numbers.update(order.number.number_id, uses=["load"])
client.numbers.release(order.number.number_id)   # billing stops
```

`client.numbers.get_requirements(country="GB")` lists what a country's regulator
asks for. nopaque supplies all of it; nothing is asked of you.

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
