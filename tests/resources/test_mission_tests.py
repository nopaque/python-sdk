"""Tests for the mission_tests resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque, NotFoundError, ServerError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_sends_expected_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={
            "id": "mt_1",
            "workspaceId": "w",
            "kind": "freeform",
            "sector": "insurance",
            "mission": "Buy a policy",
            "acceptance": "Bot offers a quote",
            "profile": {"phoneNumber": "+441234"},
            "status": "queued",
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    run = c.mission_tests.create(
        sector="insurance",
        mission="Buy a policy",
        acceptance="Bot offers a quote",
        profile={"phone_number": "+441234"},
    )
    assert run.id == "mt_1"
    assert run.kind == "freeform"
    req = httpx_mock.get_requests()[0]
    assert json.loads(req.content) == {
        "sector": "insurance",
        "mission": "Buy a policy",
        "acceptance": "Bot offers a quote",
        "profile": {"phoneNumber": "+441234"},
    }
    c.close()


def test_list_returns_paginator(httpx_mock: HTTPXMock):
    # The api's real envelope is `{runs, nextCursor}` and it pages on `cursor`.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        json={
            "runs": [
                {
                    "id": "mt_1",
                    "kind": "freeform",
                    "status": "completed",
                    "workspaceId": "w",
                    "sector": "i",
                    "mission": "m",
                    "acceptance": "a",
                    "profile": {"phoneNumber": "+44"},
                    "createdAt": "",
                    "updatedAt": "",
                }
            ],
            "nextCursor": "c2",
        },
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests?cursor=c2",
        json={"runs": [{"id": "mt_2", "workspaceId": "w", "status": "pending", "testType": "mission", "startedAt": ""}]},
    )
    c = client()
    ids = [r.id for r in c.mission_tests.list()]
    assert ids == ["mt_1", "mt_2"]
    c.close()


def test_list_parses_a_run_launched_from_a_saved_config(httpx_mock: HTTPXMock):
    # Shape of prod run 2bd58510: no kind/createdAt/updatedAt, `profile` is the
    # profile ID string, status "cancelled". The old model required all of
    # those and raised a ValidationError on real workspaces.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        json={
            "runs": [
                {
                    "id": "2bd58510",
                    "workspaceId": "w",
                    "testType": "mission",
                    "status": "cancelled",
                    "startedAt": "2026-10-15T16:41:15.941Z",
                    "completedAt": "2026-10-15T16:42:55.605Z",
                    "configId": "cfg_1",
                    "profile": "profile_abc",
                    "mission": "say hello",
                    "acceptance": "person answering says hello",
                    "sector": "test sector",
                    "phoneNumber": "+15550000000",
                    "voiceId": "Telnyx.Ultra.x",
                }
            ],
        },
    )
    c = client()
    (run,) = list(c.mission_tests.list())
    assert run.status == "cancelled"
    assert run.profile == "profile_abc"
    assert run.config_id == "cfg_1"
    assert run.kind is None
    c.close()


def test_get_defaults_returns_defaults(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/defaults",
        json={
            "sector": "insurance",
            "mission": "m",
            "acceptance": "a",
            "catalogueVersion": "v1",
        },
    )
    c = client()
    d = c.mission_tests.get_defaults()
    assert d.catalogue_version == "v1"
    c.close()


def test_get_defaults_surfaces_catalog_not_ready(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/defaults",
        status_code=503,
        json={"error": "not ready", "code": "CATALOG_NOT_READY"},
    )
    c = client()
    with pytest.raises(ServerError) as exc:
        c.mission_tests.get_defaults()
    assert exc.value.code == "CATALOG_NOT_READY"
    c.close()


def test_get_returns_a_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_1",
        json={
            "id": "mt_1",
            "kind": "freeform",
            "status": "running",
            "workspaceId": "w",
            "sector": "i",
            "mission": "m",
            "acceptance": "a",
            "profile": {"phoneNumber": "+44"},
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    run = c.mission_tests.get("mt_1")
    assert run.status == "running"
    c.close()


def test_get_cross_workspace_raises_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_other",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.mission_tests.get("mt_other")
    c.close()


def test_cancel_posts_to_cancel(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_1/cancel",
        method="POST",
        json={
            "id": "mt_1",
            "kind": "freeform",
            "status": "cancelled",
            "workspaceId": "w",
            "sector": "i",
            "mission": "m",
            "acceptance": "a",
            "profile": {"phoneNumber": "+44"},
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    r = c.mission_tests.cancel("mt_1")
    assert r.status == "cancelled"
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/testing/mission-tests/mt_1/cancel"
    assert req.method == "POST"
    c.close()


def test_list_sends_server_side_filters(httpx_mock: HTTPXMock):
    # 2026-10-15 Walgreens: "can you use the filtering with listing runs?"
    # Every filter goes to the api; nothing is filtered client-side.
    httpx_mock.add_response(
        url=(
            "https://api.nopaque.co.uk/testing/mission-tests"
            "?kind=freeform&configId=cfg_1&q=covid&phoneNumber=3301900&tags=vax%2Cregression"
        ),
        json={"runs": [{"id": "mt_1", "workspaceId": "w", "status": "completed", "configId": "cfg_1"}]},
    )
    c = client()
    runs = list(
        c.mission_tests.list(
            kind="freeform",
            config_id="cfg_1",
            q="covid",
            phone_number="3301900",
            tags=["vax", "regression"],
        )
    )
    assert [r.id for r in runs] == ["mt_1"]
    c.close()


def test_list_keeps_filters_on_every_page(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests?configId=cfg_1",
        json={"runs": [{"id": "mt_1", "workspaceId": "w", "status": "completed"}], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests?configId=cfg_1&cursor=c2",
        json={"runs": [{"id": "mt_2", "workspaceId": "w", "status": "completed"}]},
    )
    c = client()
    assert [r.id for r in c.mission_tests.list(config_id="cfg_1")] == ["mt_1", "mt_2"]
    c.close()


def test_list_page_accepts_tags_as_a_string(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests?tags=vax&limit=5",
        json={"runs": []},
    )
    c = client()
    page = c.mission_tests.list_page(tags="vax", limit=5)
    assert page.items == []
    c.close()


async def test_list_filters_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests?configId=cfg_1&kind=freeform",
        json={"runs": [{"id": "mt_1", "workspaceId": "w", "status": "completed"}]},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    ids = [r.id async for r in c.mission_tests.list(config_id="cfg_1", kind="freeform")]
    assert ids == ["mt_1"]
    await c.aclose()


# ==== Call language ==========================================================
# A mission test's call language. 11 codes from the openapi `CallLanguage`
# schema; absent means English. The contract: the key reaches the wire ONLY
# when the caller passes it, and it round-trips on the run model.

_RUN_STUB = {
    "id": "mt_1",
    "workspaceId": "w",
    "status": "queued",
    "testType": "mission",
    "startedAt": "",
}


def test_create_omits_language_when_not_passed(httpx_mock: HTTPXMock):
    """No language argument -> no `language` key at all (not `None`)."""
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json=_RUN_STUB,
    )
    c = client()
    c.mission_tests.create(
        sector="insurance",
        mission="Buy a policy",
        acceptance="Bot offers a quote",
        profile={"phone_number": "+441234"},
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert "language" not in body
    c.close()


def test_create_sends_language_when_passed(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={**_RUN_STUB, "language": "es"},
    )
    c = client()
    run = c.mission_tests.create(
        sector="insurance",
        mission="Buy a policy",
        acceptance="Bot offers a quote",
        profile={"phone_number": "+441234"},
        language="es",
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["language"] == "es"
    # and it round-trips off the response
    assert run.language == "es"
    c.close()


def test_create_sends_bare_en_as_a_valid_call_language(httpx_mock: HTTPXMock):
    """`en` is valid for the CALL language (it is rejected for transcription)."""
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={**_RUN_STUB, "language": "en"},
    )
    c = client()
    run = c.mission_tests.create(
        sector="s",
        mission="m",
        acceptance="a",
        profile={"phone_number": "+441234"},
        language="en",
    )
    assert json.loads(httpx_mock.get_requests()[0].content)["language"] == "en"
    assert run.language == "en"
    c.close()


def test_create_sends_multi_language(httpx_mock: HTTPXMock):
    """`multi` is Flux-multi: code-switches across the other ten."""
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={**_RUN_STUB, "language": "multi"},
    )
    c = client()
    run = c.mission_tests.create(
        sector="s",
        mission="m",
        acceptance="a",
        profile={"phone_number": "+441234"},
        language="multi",
    )
    assert json.loads(httpx_mock.get_requests()[0].content)["language"] == "multi"
    assert run.language == "multi"
    c.close()


def test_run_language_is_none_when_absent(httpx_mock: HTTPXMock):
    """Absent means English -> the field reads as None, never a guessed code."""
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_1",
        json=_RUN_STUB,
    )
    c = client()
    assert c.mission_tests.get("mt_1").language is None
    c.close()


async def test_create_sends_language_when_passed_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={**_RUN_STUB, "language": "fr"},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    run = await c.mission_tests.create(
        sector="s",
        mission="m",
        acceptance="a",
        profile={"phone_number": "+441234"},
        language="fr",
    )
    assert json.loads(httpx_mock.get_requests()[0].content)["language"] == "fr"
    assert run.language == "fr"
    await c.aclose()


async def test_create_omits_language_when_not_passed_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json=_RUN_STUB,
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    await c.mission_tests.create(
        sector="s",
        mission="m",
        acceptance="a",
        profile={"phone_number": "+441234"},
    )
    assert "language" not in json.loads(httpx_mock.get_requests()[0].content)
    await c.aclose()


def test_call_language_alias_is_exported():
    """The alias is part of the public surface, like MissionTestKind."""
    import typing

    from nopaque import CallLanguage

    assert set(typing.get_args(CallLanguage)) == {
        "en",
        "multi",
        "es",
        "fr",
        "de",
        "it",
        "pt",
        "nl",
        "hi",
        "ru",
        "ja",
    }
