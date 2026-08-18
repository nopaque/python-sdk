# Digital Testing Coverage (Python SDK) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 12 `/digital-testing/*` operations plus `GET /testing/voices` to the `nopaque` Python SDK, sync and async, and release it as 0.4.0.

**Architecture:** Three new flat resource modules (`digital_testing`, `digital_test_configs`, `digital_compliance`) plus one method on the existing `testing` resource, following the established one-module-per-domain layout. Models live in a new `models/digital_testing.py`. Every method is implemented twice, sync and async, as every other resource in this SDK is.

**Tech Stack:** Python 3.9+, Pydantic v2, httpx, pytest + pytest_httpx, hatch, ruff, mypy.

**Companion:** the Node SDK equivalent shipped as nopaque/node-sdk#5. Its design doc, `node-sdk/docs/superpowers/specs/2026-08-12-digital-testing-sdk-coverage-design.md`, covers the shared decisions.

## THE MOST IMPORTANT INSTRUCTION IN THIS PLAN

**Derive every model from the OpenAPI document, never from the Node SDK.**

Source of truth: `/Users/phil/code/nopaque/nopaque-v2-sdks/api/openapi/openapi.yaml`

The Node SDK's first attempt at these types was written from a partial read of that document and invented field names — `Voice.id` instead of `voiceId`, a `DigitalStepResult` sharing zero field names with the API, `DigitalSample.steps`/`reason` instead of `stepResults`/`reasoning`. It type-checked clean and would have failed silently at runtime. It was caught only when a reviewer went back to the OpenAPI document, and was rewritten in commit `d7e6eda`.

Porting from the Node types is exactly how that error propagates a second time. For each model, open the schema in `openapi.yaml`, read it in full including any `allOf`/`oneOf` composition and the `required` list, and transcribe it. The corrected Node types at `node-sdk/src/types/digitalTesting.ts` may be used as a **cross-check after** you have transcribed a model — never as the source.

Schema line references (starting points; read the whole schema, not just these lines):

| Schema | `openapi.yaml` |
| --- | --- |
| `Voice`, `ListVoicesResponse` | 2643-2699 |
| `ConnectChatTarget`, `HttpJsonTarget`, `WebWidgetTarget`, `DigitalTarget` | 6333-6425 |
| `ChatStepBase`, `SendChatStep`, `ExpectChatStep`, `WaitChatStep`, `EndChatStep`, `ChatStep` | 6427-6518 |
| `DigitalProfile` | 6520-6533 |
| `CreateDigitalTestRunRequest` | 6535-6626 |
| `DigitalStepResult` | 6627-6652 |
| `DigitalSample` | 6653-6678 |
| `DigitalTestRun` | 6679-6737 |
| `CreateDigitalTestRunResponse`, `ListDigitalTestRunsResponse` | 6738-6764 |
| `DigitalTestConfigBase`, `DigitalTestConfig`, `ListDigitalTestConfigsResponse`, `LaunchDigitalTestConfigRequest` | 6792-6926 |
| digital compliance audit paths (inline schemas) | 16094-16200 |

## Global Constraints

- **Target Python 3.9.** In `models/`, use `Optional[X]`, `List[X]`, `Union[X, Y]` from `typing` — **never** PEP 585/604 syntax (`list[str]`, `X | None`). Pydantic models are runtime-evaluated and that syntax needs 3.10+. `UP006`, `UP007`, `UP035` and `UP045` are in the ruff ignore list for exactly this reason. Do not "modernise" them.
  - Note the asymmetry: non-model modules (`_pagination.py`, resources) DO use `str | None`, because they carry `from __future__ import annotations` and their annotations are never evaluated at runtime. Match whichever convention the file you are editing already uses.
- **Line length is 100** (`[tool.ruff] line-length = 100`).
- **Models are snake_case with a camelCase alias map.** Each model module defines `_ALIAS_MAP: dict[str, str]` and `def _alias(name)`, and the module's private base class sets `model_config = ConfigDict(extra="allow", populate_by_name=True, alias_generator=_alias)`. Follow `src/nopaque/models/mapping.py` exactly.
- **Resource methods take keyword-only arguments**, not a body dict. They build a request model, then `.model_dump(by_alias=True, exclude_none=True)`. See `src/nopaque/resources/mission_test_configs.py:196-225`.
- **Every method is implemented twice**, sync and async, in separate classes in the same module.
- **Async mode is automatic** (`asyncio_mode = "auto"`) — async tests need no marker.
- **Version lives only in `src/nopaque/_version.py`** and is read dynamically by hatch. Do not hardcode it anywhere else.
- **Do not modify `src/nopaque/_pagination.py`.** Cursor translation happens in each resource via a module-level `_apply_cursor` helper.
- **Beta wording, verbatim from the OpenAPI document:** "Beta. Access is limited to beta workspaces during the beta period." Every digital-testing method's docstring opens with it.
- **`list_voices` is not a beta operation.** No beta note in its docstring.
- Full gate before opening the PR: `hatch run lint && hatch run type && hatch run test`.
- Branch from `main`, PR against `main`.

---

### Task 1: Models

**Files:**
- Create: `src/nopaque/models/digital_testing.py`
- Modify: `src/nopaque/models/testing.py` (add `Voice`, `ListVoicesResponse`)
- Modify: `src/nopaque/models/__init__.py` (re-export)

**Interfaces:**
- Consumes: nothing.
- Produces: every model the later tasks import.

Transcribe from `openapi.yaml` per the instruction at the top of this plan. The
model names to produce, and the constraints on each, are below. Field names and
optionality come from the document, not from this table.

| Model | Notes |
| --- | --- |
| `ConnectChatTarget`, `HttpJsonTarget`, `WebWidgetTarget` | Each has a `transport` `Literal` discriminator value. |
| `DigitalTarget` | `Annotated[Union[...], Field(discriminator="transport")]` |
| `ChatStepBase` | optional `id`, `name`; the four step types compose it |
| `SendChatStep`, `ExpectChatStep`, `WaitChatStep`, `EndChatStep` | each with a `type` `Literal` |
| `ChatStep` | `Annotated[Union[...], Field(discriminator="type")]` |
| `DigitalProfileItem`, `DigitalProfile` | profile is `{dataItems: Dict[str, DigitalProfileItem]}` |
| `DigitalStepResult`, `DigitalSample`, `DigitalTestRun` | response models |
| `DigitalTestConfigBase`, `DigitalTestConfig` | config is the base plus server-set fields |
| `CreateDigitalTestRunRequest`, `CreateDigitalTestConfigRequest`, `UpdateDigitalTestConfigRequest`, `LaunchDigitalTestConfigRequest` | request models |
| `CreateDigitalTestRunResponse`, `ListDigitalTestRunsResponse`, `ListDigitalTestConfigsResponse` | envelopes |
| `DigitalComplianceAuditSummary`, `ListDigitalComplianceAuditsResponse` | inline in the document; you name them |
| `Voice`, `ListVoicesResponse` | into `models/testing.py`, NOT the digital module |

Two things need care:

**Discriminated unions are new to this SDK.** No model in `src/nopaque/models/`
currently uses one — grep confirms zero `discriminator` occurrences. You are
establishing the pattern. Under Pydantic v2 on a 3.9 target:

```python
from typing import Union

from pydantic import Field
from typing_extensions import Annotated

DigitalTarget = Annotated[
    Union[ConnectChatTarget, HttpJsonTarget, WebWidgetTarget],
    Field(discriminator="transport"),
]
```

Import `Annotated` from `typing_extensions`, not `typing` — `typing.Annotated`
exists in 3.9 but `typing_extensions` is the safer source across the supported
range, and check whether the project already depends on it before adding an
import. If it does not, use `typing.Annotated` (available since 3.9) instead.

**`SendChatStep` needs a validator, not a type trick.** The API requires
`type`, and accepts *exactly one* of `text` or `profileItemId` — the API-side
rule is `.refine(Boolean(text) !== Boolean(profileItemId))`. Model both as
`Optional[str]` and enforce the either/or with a Pydantic `model_validator`:

```python
    @model_validator(mode="after")
    def _exactly_one_source(self) -> "SendChatStep":
        if (self.text is None) == (self.profile_item_id is None):
            raise ValueError("send step needs exactly one of text or profile_item_id")
        return self
```

- [ ] **Step 1: Write the models**

Transcribe each schema. Follow `src/nopaque/models/mapping.py` for module
layout: `_ALIAS_MAP`, `_alias`, a private base class with the `ConfigDict`, then
the models. Every camelCase API field needs an entry in `_ALIAS_MAP`.

- [ ] **Step 2: Write model tests**

Create `tests/test_digital_models.py`. Build every fixture from the OpenAPI
schemas' documented shapes and `example` values — **not** from your own model
definitions. A test that round-trips your models against themselves proves
nothing, which is precisely how the Node defects survived a green suite.

Cover at minimum:

```python
def test_digital_target_discriminates_on_transport():
    t = DigitalTarget_adapter.validate_python(
        {"transport": "web-widget", "url": "https://example.com/support"}
    )
    assert isinstance(t, WebWidgetTarget)


def test_send_step_accepts_profile_item_id():
    s = SendChatStep.model_validate({"type": "send", "profileItemId": "accountNumber"})
    assert s.profile_item_id == "accountNumber"


def test_send_step_rejects_both_text_and_profile_item_id():
    with pytest.raises(ValidationError):
        SendChatStep.model_validate(
            {"type": "send", "text": "hi", "profileItemId": "accountNumber"}
        )


def test_send_step_rejects_neither():
    with pytest.raises(ValidationError):
        SendChatStep.model_validate({"type": "send"})


def test_run_parses_camel_case_from_the_wire():
    run = DigitalTestRun.model_validate({
        "id": "r1",
        "workspaceId": "w1",
        "targetRef": "acme/billing-bot",
        "channel": "chat",
        "kind": "freeform",
        "status": "completed",
        "startedAt": "2026-08-12T00:00:00Z",
        "outcome": "fail",
        "samples": [{"stepResults": [], "reasoning": "bot never stated the balance"}],
    })
    assert run.workspace_id == "w1"
    assert run.samples[0].reasoning == "bot never stated the balance"
```

Use `pydantic.TypeAdapter` for the union types, since a bare `Annotated` alias
has no `.model_validate`.

- [ ] **Step 3: Run the gate**

```bash
hatch run lint
hatch run type
hatch run test
```

Expected: all three pass.

- [ ] **Step 4: Commit**

```bash
git add src/nopaque/models/digital_testing.py src/nopaque/models/testing.py src/nopaque/models/__init__.py tests/test_digital_models.py
git commit -m "feat(models): add digital testing and voice models"
```

---

### Task 2: `list_voices` on the testing resource

**Files:**
- Modify: `src/nopaque/resources/testing.py`
- Test: `tests/resources/test_testing.py`

**Interfaces:**
- Consumes: `ListVoicesResponse` from Task 1.
- Produces: `client.testing.list_voices(*, request_options=None) -> ListVoicesResponse`, sync and async.

The smallest end-to-end slice, proving the wiring before larger resources land.

- [ ] **Step 1: Write the failing tests**

Append to `tests/resources/test_testing.py`:

```python
def test_list_voices(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/voices",
        json={
            "voices": [
                {
                    "voiceId": "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae",
                    "name": "Ultra",
                }
            ],
            "defaultVoiceId": "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae",
        },
    )
    c = client()
    r = c.testing.list_voices()
    assert r.voices[0].voice_id.startswith("Telnyx.")
    assert r.default_voice_id == r.voices[0].voice_id
    c.close()


async def test_list_voices_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/voices",
        json={"voices": [{"voiceId": "v1", "name": "Ultra"}]},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.testing.list_voices()
    assert r.voices[0].voice_id == "v1"
    await c.aclose()
```

Check the top of the existing test file for how it imports and constructs the
async client, and match it — the names above are the expected ones but verify.

- [ ] **Step 2: Run and confirm failure**

Run: `hatch run test -- tests/resources/test_testing.py -k list_voices`
Expected: FAIL, no attribute `list_voices`.

- [ ] **Step 3: Implement**

Add to both `TestingResource` and `AsyncTestingResource` in
`src/nopaque/resources/testing.py`. There is no beta note — this is a GA
operation.

```python
    def list_voices(
        self,
        *,
        request_options: RequestOptions | None = None,
    ) -> ListVoicesResponse:
        """Operator-enabled voices a mission test may use, and which is default."""
        raw = self._transport.request(
            "GET", "/testing/voices", request_options=request_options
        )
        return ListVoicesResponse.model_validate(raw)
```

The async flavour is the same with `async def` and `await self._transport.request(...)`.

- [ ] **Step 4: Run and confirm pass**

Run: `hatch run test -- tests/resources/test_testing.py`
Expected: PASS, including the file's pre-existing tests.

- [ ] **Step 5: Commit**

```bash
git add src/nopaque/resources/testing.py tests/resources/test_testing.py
git commit -m "feat(testing): add list_voices"
```

---

### Task 3: `digital_testing` resource — runs

**Files:**
- Create: `src/nopaque/resources/digital_testing.py`
- Create: `tests/resources/test_digital_testing.py`
- Modify: `src/nopaque/_client.py`

**Interfaces:**
- Consumes: Task 1 models.
- Produces, on both `client.digital_testing` and the async client:
  - `create(*, target_ref, target, sector, mission, kind=..., acceptance=None, ..., request_options=None) -> DigitalTestRun`
  - `list(*, target_ref=None, limit=None, cursor=None, next_token=None, request_options=None) -> SyncPaginator[DigitalTestRun]`
  - `list_page(...) -> Page[DigitalTestRun]`
  - `get(run_id, *, request_options=None) -> DigitalTestRun`
  - `cancel(run_id, *, request_options=None) -> DigitalTestRun`
  - `wait_for_run(run_id, *, timeout=..., poll_interval=..., interval_cap=..., on_update=None, request_options=None) -> DigitalTestRun`

Three points to implement exactly:

1. **`sector` and `mission` are REQUIRED on run creation** (`openapi.yaml:6536`,
   enforced at `api/packages/functions/digital-testing/runs.ts:43-44`). Make them
   required keyword arguments, not optional. The Node SDK shipped them optional
   at first and its README example was a guaranteed 400.
2. **`wait_for_run` resolves on `completed`, `failed` AND `cancelled`**, and
   returns the run. A run that is `completed` with `outcome="fail"` is a
   badly-behaved bot — a RESULT, not an error. It must not raise. `failed`
   separately means the test could not be delivered.
3. **Cursor translation uses a module-level `_apply_cursor`**, copied from
   `src/nopaque/resources/testing.py:70-75`. It pops the paginator's injected
   `nextToken` and writes it to `cursor`, which correctly overrides any
   caller-supplied starting cursor on later pages.

- [ ] **Step 1: Write the failing tests**

Create `tests/resources/test_digital_testing.py`. Build fixtures from the
OpenAPI schemas, not from your models.

Header and helpers, matching the convention in
`tests/resources/test_mission_test_configs.py`:

```python
"""Tests for the digital testing resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque, NopaqueTimeoutError

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


def run_json(**over):
    """Shaped from the OpenAPI DigitalTestRun schema, camelCase as the wire sends it."""
    doc = {
        "id": "r1",
        "workspaceId": "w1",
        "targetRef": "acme/billing-bot",
        "channel": "chat",
        "kind": "freeform",
        "status": "pending",
        "startedAt": "2026-08-12T00:00:00Z",
    }
    doc.update(over)
    return doc
```

Then these tests. Write every one — they are the task's gate:

```python
def test_create_unwraps_envelope_and_sends_camel_case(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        method="POST",
        json={"message": "Digital test queued", "run": run_json()},
    )
    c = client()
    r = c.digital_testing.create(
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
        kind="freeform",
        acceptance="The bot states the outstanding balance.",
    )
    assert r.id == "r1"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["targetRef"] == "acme/billing-bot"
    assert sent["target"]["transport"] == "web-widget"
    assert "target_ref" not in sent
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1", json=run_json(status="completed")
    )
    c = client()
    assert c.digital_testing.get("r1").status == "completed"
    c.close()


def test_cancel_posts(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1/cancel",
        method="POST",
        json=run_json(status="cancelled"),
    )
    c = client()
    assert c.digital_testing.cancel("r1").status == "cancelled"
    c.close()


def test_list_walks_pages_via_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?limit=2",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?limit=2&cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = client()
    assert [r.id for r in c.digital_testing.list(limit=2)] == ["r1", "r2"]
    c.close()


def test_list_with_explicit_cursor_advances(httpx_mock: HTTPXMock):
    """A caller-supplied starting cursor must not pin every page to page one."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c1",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = client()
    assert [r.id for r in c.digital_testing.list(cursor="c1")] == ["r1", "r2"]
    c.close()


def test_list_page_maps_runs_and_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        json={"runs": [run_json()], "nextCursor": "c2"},
    )
    c = client()
    page = c.digital_testing.list_page()
    assert len(page.items) == 1
    assert page.next_token == "c2"
    c.close()


def test_wait_for_run_returns_on_completed_even_when_outcome_is_fail(httpx_mock: HTTPXMock):
    """A badly-behaved bot is a RESULT, not an error. This must not raise."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1",
        json=run_json(status="completed", outcome="fail", passRate=0.25),
    )
    c = client()
    r = c.digital_testing.wait_for_run("r1", poll_interval=0.001)
    assert r.status == "completed"
    assert r.outcome == "fail"
    assert r.pass_rate == 0.25
    c.close()


def test_wait_for_run_returns_on_cancelled(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1", json=run_json(status="cancelled")
    )
    c = client()
    assert c.digital_testing.wait_for_run("r1", poll_interval=0.001).status == "cancelled"
    c.close()


def test_wait_for_run_returns_on_failed_with_reason(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1",
        json=run_json(status="failed", failureReason="transport timeout"),
    )
    c = client()
    r = c.digital_testing.wait_for_run("r1", poll_interval=0.001)
    assert r.failure_reason == "transport timeout"
    c.close()


def test_wait_for_run_times_out(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1", json=run_json(status="running")
    )
    c = client()
    with pytest.raises(NopaqueTimeoutError):
        c.digital_testing.wait_for_run("r1", timeout=0.05, poll_interval=0.01)
    c.close()


async def test_create_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        method="POST",
        json={"message": "Digital test queued", "run": run_json()},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_testing.create(
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
    )
    assert r.id == "r1"
    await c.aclose()


async def test_list_async_walks_pages(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    seen = [r.id async for r in c.digital_testing.list()]
    assert seen == ["r1", "r2"]
    await c.aclose()
```

If `httpx_mock` URL matching turns out to be stricter or looser about query
strings than the above assumes, adjust the matching style to whatever the
existing tests in `tests/resources/` already do — but keep every assertion.

- [ ] **Step 2: Run and confirm failure**

Run: `hatch run test -- tests/resources/test_digital_testing.py`
Expected: FAIL, `digital_testing` attribute missing.

- [ ] **Step 3: Implement the resource**

Follow `src/nopaque/resources/mission_test_configs.py` for structure: module
docstring, imports, `_ALIAS`-free (models own aliasing), `_apply_cursor`, then
`DigitalTestingResource(SyncResource)` and `AsyncDigitalTestingResource(AsyncResource)`.

Every method's docstring opens with the beta line:

```python
        """Queue a digital (chat) test run.

        Beta. Access is limited to beta workspaces during the beta period.
        """
```

`wait_for_run` uses `wait_for_sync` / `wait_for_async` from `.._polling`, mapping
`poll_interval` to the helper's `initial_interval`, as `batches.py` does.

- [ ] **Step 4: Wire into the client**

In `src/nopaque/_client.py`, add `self.digital_testing = DigitalTestingResource(self._transport)`
to `Nopaque.__init__` and `self.digital_testing = AsyncDigitalTestingResource(self._transport)`
to `AsyncNopaque.__init__`, each in the same relative position as the other
resources, with the imports at the top.

- [ ] **Step 5: Run the gate**

```bash
hatch run test -- tests/resources/test_digital_testing.py
hatch run test
hatch run lint
hatch run type
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/nopaque/resources/digital_testing.py src/nopaque/_client.py tests/resources/test_digital_testing.py
git commit -m "feat(digital-testing): add run resource, sync and async"
```

---

### Task 4: `digital_test_configs` resource

**Files:**
- Create: `src/nopaque/resources/digital_test_configs.py`
- Create: `tests/resources/test_digital_test_configs.py`
- Modify: `src/nopaque/_client.py`

**Interfaces:**
- Consumes: Task 1 models; `DigitalTestRun` for `launch`.
- Produces, sync and async: `list`, `list_page`, `create`, `get`, `update`, `delete`, `launch`.

Points to implement exactly:

1. **`update` uses HTTP PATCH**, not PUT. The voice `_SyncConfigs.update` in
   `testing.py` uses PUT — this differs deliberately, because the API defines
   PATCH for digital configs.
2. **`launch` POSTs to `/digital-testing/configs/{id}/runs`** and unwraps the
   `{message, run}` envelope, returning a `DigitalTestRun`.
3. **`target_ref` and `target` must be overridden together** on launch — a
   half-override is a 400 server-side. Do not enforce it client-side, but say so
   in the docstring.
4. The list response uses a **`configs`** collection key with `cursor`/`nextCursor`.
5. `sector` and `mission` are required on config creation too — check the
   `CreateDigitalTestConfigRequest` schema and match it.

- [ ] **Step 1: Write the failing tests**

Create `tests/resources/test_digital_test_configs.py`, fixtures from the OpenAPI
schemas:

```python
"""Tests for the digital test configs resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


def cfg_json(**over):
    """Shaped from the OpenAPI DigitalTestConfig schema."""
    doc = {
        "id": "c1",
        "workspaceId": "w1",
        "name": "Billing bot smoke",
        "targetRef": "acme/billing-bot",
        "target": {"transport": "web-widget", "url": "https://example.com/support"},
        "sector": "utilities",
        "mission": "check the outstanding balance",
        "kind": "freeform",
        "createdAt": "2026-08-12T00:00:00Z",
        "updatedAt": "2026-08-12T00:00:00Z",
    }
    doc.update(over)
    return doc


def test_create_posts(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs", method="POST", json=cfg_json()
    )
    c = client()
    r = c.digital_test_configs.create(
        name="Billing bot smoke",
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
    )
    assert r.id == "c1"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["targetRef"] == "acme/billing-bot"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/digital-testing/configs/c1", json=cfg_json())
    c = client()
    assert c.digital_test_configs.get("c1").name == "Billing bot smoke"
    c.close()


def test_update_uses_patch_not_put(httpx_mock: HTTPXMock):
    """The voice config resource uses PUT. Digital deliberately uses PATCH."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1",
        method="PATCH",
        json=cfg_json(name="Renamed"),
    )
    c = client()
    r = c.digital_test_configs.update("c1", name="Renamed")
    assert r.name == "Renamed"
    assert httpx_mock.get_requests()[0].method == "PATCH"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1", method="DELETE", status_code=204
    )
    c = client()
    assert c.digital_test_configs.delete("c1") is None
    assert httpx_mock.get_requests()[0].method == "DELETE"
    c.close()


def test_launch_posts_to_runs_subpath_and_unwraps(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1/runs",
        method="POST",
        json={
            "message": "Digital test queued",
            "run": {
                "id": "r9",
                "workspaceId": "w1",
                "targetRef": "acme/billing-bot",
                "channel": "chat",
                "kind": "freeform",
                "status": "pending",
                "startedAt": "2026-08-12T00:00:00Z",
            },
        },
    )
    c = client()
    assert c.digital_test_configs.launch("c1", samples=3).id == "r9"
    c.close()


def test_list_walks_pages_via_configs_key(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs",
        json={"configs": [cfg_json(id="c1")], "nextCursor": "n2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n2",
        json={"configs": [cfg_json(id="c2")]},
    )
    c = client()
    assert [x.id for x in c.digital_test_configs.list()] == ["c1", "c2"]
    c.close()


def test_list_with_explicit_cursor_advances(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n1",
        json={"configs": [cfg_json(id="c1")], "nextCursor": "n2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n2",
        json={"configs": [cfg_json(id="c2")]},
    )
    c = client()
    assert [x.id for x in c.digital_test_configs.list(cursor="n1")] == ["c1", "c2"]
    c.close()


def test_list_page_maps_configs_and_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs",
        json={"configs": [cfg_json()], "nextCursor": "n2"},
    )
    c = client()
    page = c.digital_test_configs.list_page()
    assert len(page.items) == 1
    assert page.next_token == "n2"
    c.close()


async def test_update_async_uses_patch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1",
        method="PATCH",
        json=cfg_json(name="Renamed"),
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_test_configs.update("c1", name="Renamed")
    assert r.name == "Renamed"
    await c.aclose()


async def test_launch_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1/runs",
        method="POST",
        json={
            "run": {
                "id": "r9",
                "workspaceId": "w1",
                "targetRef": "acme/billing-bot",
                "channel": "chat",
                "kind": "freeform",
                "status": "pending",
                "startedAt": "2026-08-12T00:00:00Z",
            }
        },
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    assert (await c.digital_test_configs.launch("c1")).id == "r9"
    await c.aclose()
```

- [ ] **Step 2: Run and confirm failure**

Run: `hatch run test -- tests/resources/test_digital_test_configs.py`
Expected: FAIL, attribute missing.

- [ ] **Step 3: Implement, mirroring Task 3's module structure**

Beta docstrings on every method. Sync and async classes.

- [ ] **Step 4: Wire into the client**, both sync and async, as in Task 3.

- [ ] **Step 5: Run the gate**

```bash
hatch run test -- tests/resources/test_digital_test_configs.py
hatch run test
hatch run lint
hatch run type
```

- [ ] **Step 6: Commit**

```bash
git add src/nopaque/resources/digital_test_configs.py src/nopaque/_client.py tests/resources/test_digital_test_configs.py
git commit -m "feat(digital-testing): add saved config resource, sync and async"
```

---

### Task 5: `digital_compliance` resource

**Files:**
- Create: `src/nopaque/resources/digital_compliance.py`
- Create: `tests/resources/test_digital_compliance.py`
- Modify: `src/nopaque/_client.py`

**Interfaces:**
- Consumes: `DigitalComplianceAuditSummary` from Task 1.
- Produces, sync and async:
  - `list_audits(*, request_options=None) -> List[DigitalComplianceAuditSummary]`
  - `get_report(*, target_ref, sector=None, request_options=None) -> Any`

Points to implement exactly:

1. **`target_ref` goes in the QUERY STRING, never the path.** A `targetRef`
   looks like `acme/billing-bot` — it contains a slash and a single path segment
   cannot hold one. The API defines it as a query param for this reason. A test
   must pin it, including asserting the URL does not contain `report/acme`.
2. **`get_report` returns the parsed body as-is** (`Any`). The report body is not
   a named schema in the OpenAPI document, so do not invent a model that could
   drift from the server.
3. **`list_audits` is NOT paginated** — it returns the whole set. Return a plain
   list, not a paginator. Unwrap the `{audits: [...]}` envelope, defaulting to `[]`.
4. `sector` is an optional query filter on the report endpoint
   (`openapi.yaml:16188-16193`).

- [ ] **Step 1: Write the failing tests**

Create `tests/resources/test_digital_compliance.py`:

```python
"""Tests for the digital compliance resource."""
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


AUDIT = {
    "targetRef": "acme/billing-bot",
    "lastRunAt": "2026-08-12T00:00:00Z",
    "runCount": 4,
    "catalogueTestIds": ["M-001"],
}


def test_list_audits_unwraps_envelope(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits", json={"audits": [AUDIT]}
    )
    c = client()
    r = c.digital_compliance.list_audits()
    assert len(r) == 1
    assert r[0].run_count == 4
    assert r[0].target_ref == "acme/billing-bot"
    c.close()


def test_list_audits_returns_empty_when_key_absent(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/digital-testing/compliance-audits", json={})
    c = client()
    assert c.digital_compliance.list_audits() == []
    c.close()


def test_get_report_sends_target_ref_as_query_never_path(httpx_mock: HTTPXMock):
    """A targetRef contains slashes, so it cannot be a path segment."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report?targetRef=acme%2Fbilling-bot",
        json={"targetRef": "acme/billing-bot"},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/billing-bot")
    url = str(httpx_mock.get_requests()[0].url)
    assert "/digital-testing/compliance-audits/report" in url
    assert "targetRef=acme%2Fbilling-bot" in url
    assert "report/acme" not in url
    c.close()


def test_get_report_includes_sector_when_given(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report"
        "?targetRef=acme%2Fbilling-bot&sector=utilities",
        json={},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/billing-bot", sector="utilities")
    assert "sector=utilities" in str(httpx_mock.get_requests()[0].url)
    c.close()


def test_get_report_omits_sector_when_not_given(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report?targetRef=acme%2Fbot",
        json={},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/bot")
    assert "sector" not in str(httpx_mock.get_requests()[0].url)
    c.close()


async def test_list_audits_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits", json={"audits": [AUDIT]}
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_compliance.list_audits()
    assert r[0].run_count == 4
    await c.aclose()
```

- [ ] **Step 2: Run and confirm failure**

Run: `hatch run test -- tests/resources/test_digital_compliance.py`
Expected: FAIL, attribute missing.

- [ ] **Step 3: Implement**, sync and async, beta docstrings on both methods.

- [ ] **Step 4: Wire into the client**, both flavours.

- [ ] **Step 5: Run the gate**

```bash
hatch run test -- tests/resources/test_digital_compliance.py
hatch run test
hatch run lint
hatch run type
```

- [ ] **Step 6: Commit**

```bash
git add src/nopaque/resources/digital_compliance.py src/nopaque/_client.py tests/resources/test_digital_compliance.py
git commit -m "feat(digital-testing): add compliance audit resource, sync and async"
```

---

### Task 6: Release 0.4.0

**Files:**
- Modify: `src/nopaque/_version.py`, `CHANGELOG.md`, `README.md`

**Interfaces:**
- Consumes: Tasks 1-5.
- Produces: a releasable 0.4.0.

- [ ] **Step 1: Run the full gate**

```bash
hatch run lint
hatch run type
hatch run test
python -m build
```

- [ ] **Step 2: Bump the version**

In `src/nopaque/_version.py`, change the version to `0.4.0`. It lives nowhere
else — hatch reads it dynamically.

- [ ] **Step 3: Add the changelog entry**

Read `CHANGELOG.md` first and match its established heading format exactly rather
than assuming one. Content:

```markdown
### Added

- Digital (chat channel) testing, in beta. Access is limited to beta workspaces
  during the beta period.
  - `client.digital_testing` — create, list, get, cancel and wait for digital test runs.
  - `client.digital_test_configs` — save, update, delete and launch reusable digital test configs.
  - `client.digital_compliance` — list digital compliance audits and fetch a per-target report.
- `client.testing.list_voices()` — the operator-enabled voices a mission test may
  use, and which one is the default.

All new methods are available on both the sync and async clients.
```

- [ ] **Step 4: Document in the README**

Match the surrounding section style. The example must include `sector` and
`mission` — they are required, and an example without them is a guaranteed 400.
Verify by running the snippet's construction path, not by eye:

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

- [ ] **Step 5: Re-run the gate and commit**

```bash
hatch run lint && hatch run type && hatch run test && python -m build
git add src/nopaque/_version.py CHANGELOG.md README.md
git commit -m "chore(release): 0.4.0"
```

- [ ] **Step 6: STOP**

Do not push and do not open a PR. Report completion instead.

---

## Companion work

- **Node SDK:** shipped as nopaque/node-sdk#5.
- **OpenAPI version bump:** `api/openapi/openapi.yaml` `version: "0.3.0"` -> `"0.4.0"`, its own PR against `nopaque/api`.

## Known items carried from the Node review

Not blocking this plan, but a reviewer should know:

- `DigitalSample.transcript` is typed as a string per the OpenAPI document, but
  the API repo comments that transcript is a **list of turns**
  (`api/packages/schemas/queue/digital-test-response-queue.ts:60-77`) and records
  a prior hand-written schema getting this wrong. Transcribe what the OpenAPI
  says and flag it; do not guess.
- The digital-testing paths document no `402` response despite `BillingError`
  existing, which is the likeliest error a beta user hits.
- `DigitalStepResult.outcome` is a bare string in the document while
  `DigitalSample.outcome` is an enum. Transcribe each as written.
