"""Model tests for the digital-testing (chat channel) models and the voice models.

Every fixture below is built from the shapes and `example` values documented in
`openapi/openapi.yaml` (schemas `DigitalTarget` .. `LaunchDigitalTestConfigRequest`,
the inline `/digital-testing/compliance-audits` response, and `Voice` /
`ListVoicesResponse`) — deliberately NOT from the model definitions themselves.
"""
import pytest
from pydantic import TypeAdapter, ValidationError

from nopaque.models import (
    ChatStep,
    ConnectChatTarget,
    CreateDigitalTestConfigRequest,
    CreateDigitalTestRunRequest,
    CreateDigitalTestRunResponse,
    DigitalProfile,
    DigitalTarget,
    DigitalTestConfig,
    DigitalTestRun,
    EndChatStep,
    ExpectChatStep,
    HttpJsonTarget,
    LaunchDigitalTestConfigRequest,
    ListDigitalComplianceAuditsResponse,
    ListDigitalTestConfigsResponse,
    ListDigitalTestRunsResponse,
    ListVoicesResponse,
    SendChatStep,
    UpdateDigitalTestConfigRequest,
    Voice,
    WaitChatStep,
    WebWidgetTarget,
)

digital_target_adapter = TypeAdapter(DigitalTarget)
chat_step_adapter = TypeAdapter(ChatStep)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def test_digital_target_discriminates_on_transport():
    t = digital_target_adapter.validate_python(
        {"transport": "web-widget", "url": "https://example.com/support"}
    )
    assert isinstance(t, WebWidgetTarget)
    assert t.url == "https://example.com/support"


def test_connect_chat_target_parses_camel_case():
    t = digital_target_adapter.validate_python(
        {
            "transport": "connect-chat",
            "instanceId": "<connect-instance-id>",
            "contactFlowId": "<contact-flow-id>",
            "region": "us-east-1",
            "attributes": {"customerId": "42"},
            "assumeRoleArn": "arn:aws:iam::123456789012:role/nopaque",
        }
    )
    assert isinstance(t, ConnectChatTarget)
    assert t.instance_id == "<connect-instance-id>"
    assert t.contact_flow_id == "<contact-flow-id>"
    assert t.attributes == {"customerId": "42"}
    assert t.assume_role_arn == "arn:aws:iam::123456789012:role/nopaque"


def test_http_json_target_parses_camel_case():
    t = digital_target_adapter.validate_python(
        {
            "transport": "http-json",
            "endpoint": "https://bot.example.com/v1/chat",
            "openaiCompatible": True,
            "authRef": "secret-ref",
        }
    )
    assert isinstance(t, HttpJsonTarget)
    assert t.endpoint == "https://bot.example.com/v1/chat"
    assert t.openai_compatible is True
    assert t.auth_ref == "secret-ref"


def test_target_serialises_back_to_camel_case():
    t = digital_target_adapter.validate_python(
        {"transport": "connect-chat", "instanceId": "i-1", "contactFlowId": "f-1"}
    )
    assert t.model_dump(by_alias=True, exclude_none=True) == {
        "transport": "connect-chat",
        "instanceId": "i-1",
        "contactFlowId": "f-1",
    }


def test_target_rejects_unknown_transport():
    with pytest.raises(ValidationError):
        digital_target_adapter.validate_python({"transport": "sms", "url": "https://x"})


def test_connect_chat_target_requires_instance_and_flow():
    with pytest.raises(ValidationError):
        digital_target_adapter.validate_python({"transport": "connect-chat"})


# ---------------------------------------------------------------------------
# Chat steps
# ---------------------------------------------------------------------------


def test_send_step_accepts_profile_item_id():
    s = SendChatStep.model_validate({"type": "send", "profileItemId": "accountNumber"})
    assert s.profile_item_id == "accountNumber"


def test_send_step_accepts_text():
    s = SendChatStep.model_validate({"type": "send", "text": "hi", "name": "greeting"})
    assert s.text == "hi"
    assert s.name == "greeting"


def test_send_step_rejects_both_text_and_profile_item_id():
    with pytest.raises(ValidationError):
        SendChatStep.model_validate(
            {"type": "send", "text": "hi", "profileItemId": "accountNumber"}
        )


def test_send_step_rejects_neither():
    with pytest.raises(ValidationError):
        SendChatStep.model_validate({"type": "send"})


def test_chat_step_discriminates_on_type():
    steps = [
        {"type": "send", "text": "hello"},
        {"type": "expect", "expected": "How can I help?"},
        {"type": "wait", "seconds": 2},
        {"type": "end"},
    ]
    parsed = [chat_step_adapter.validate_python(s) for s in steps]
    assert [type(s) for s in parsed] == [
        SendChatStep,
        ExpectChatStep,
        WaitChatStep,
        EndChatStep,
    ]


def test_expect_step_carries_matcher_threshold_and_timeout():
    s = chat_step_adapter.validate_python(
        {
            "id": "s2",
            "type": "expect",
            "expected": "Your balance is £42.00",
            "matcher": "similarity",
            "threshold": 80,
            "timeoutSecs": 30,
        }
    )
    assert isinstance(s, ExpectChatStep)
    assert s.id == "s2"
    assert s.matcher == "similarity"
    assert s.threshold == 80
    assert s.timeout_secs == 30


def test_expect_step_requires_expected():
    with pytest.raises(ValidationError):
        chat_step_adapter.validate_python({"type": "expect"})


def test_expect_step_rejects_unknown_matcher():
    with pytest.raises(ValidationError):
        chat_step_adapter.validate_python(
            {"type": "expect", "expected": "hi", "matcher": "fuzzy"}
        )


def test_chat_step_rejects_unknown_type():
    with pytest.raises(ValidationError):
        chat_step_adapter.validate_python({"type": "hangup"})


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def test_digital_profile_holds_a_dict_of_data_items():
    p = DigitalProfile.model_validate(
        {"dataItems": {"accountNumber": {"label": "Account number", "value": "12345678"}}}
    )
    assert p.data_items is not None
    assert p.data_items["accountNumber"].label == "Account number"
    assert p.data_items["accountNumber"].value == "12345678"


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def test_run_parses_camel_case_from_the_wire():
    run = DigitalTestRun.model_validate(
        {
            "id": "r1",
            "workspaceId": "w1",
            "targetRef": "acme/billing-bot",
            "channel": "chat",
            "kind": "freeform",
            "status": "completed",
            "startedAt": "2026-08-12T00:00:00Z",
            "outcome": "fail",
            "samples": [
                {"stepResults": [], "reasoning": "bot never stated the balance"}
            ],
        }
    )
    assert run.workspace_id == "w1"
    assert run.target_ref == "acme/billing-bot"
    assert run.samples is not None
    assert run.samples[0].reasoning == "bot never stated the balance"


def test_run_parses_the_full_documented_shape():
    run = DigitalTestRun.model_validate(
        {
            "id": "3f0a1a2e-0000-4000-8000-000000000001",
            "workspaceId": "w1",
            "userId": "u1",
            "targetRef": "acme/billing-bot",
            "channel": "chat",
            "target": {"transport": "web-widget", "url": "https://example.com/support"},
            "kind": "standard",
            "sector": "utilities",
            "mission": "Pay my bill",
            "acceptance": "The bot states the balance",
            "catalogueTestId": "M-001",
            "status": "completed",
            "outcome": "pass",
            "samplesRequested": 3,
            "samplesJudged": 2,
            "passed": 2,
            "failed": 0,
            "transportErrors": 1,
            "passRate": 1.0,
            "sampleOutcomes": ["pass", "pass"],
            "samples": [
                {
                    "outcome": "pass",
                    "stepResults": [
                        {
                            "stepId": "s1",
                            "name": "greeting",
                            "actionType": "expect",
                            "actionValue": "hello",
                            "expectedTranscript": "Hello there",
                            "actualTranscript": "Hello there",
                            "similarity": 100,
                            "threshold": 100,
                            "outcome": "pass",
                            "duration": 0.42,
                        }
                    ],
                    "stepsRun": 1,
                    "stepsTotal": 1,
                    "transcript": "customer: hi\nbot: Hello there",
                    "reasoning": "matched",
                    "evidence": ["bot greeted the customer"],
                    "failureReason": None,
                }
            ],
            "payloadS3Bucket": "nopaque-results",
            "payloadS3Key": "digital/r1.json",
            "payloadBytes": 1024,
            "failureReason": None,
            "startedAt": "2026-08-12T00:00:00Z",
            "completedAt": "2026-08-12T00:01:00Z",
            "launchDeadline": "2026-08-12T00:05:00Z",
        }
    )
    assert run.samples_requested == 3
    assert run.samples_judged == 2
    assert run.transport_errors == 1
    assert run.pass_rate == 1.0
    assert run.sample_outcomes == ["pass", "pass"]
    assert run.payload_s3_bucket == "nopaque-results"
    assert run.payload_s3_key == "digital/r1.json"
    assert run.payload_bytes == 1024
    assert run.launch_deadline == "2026-08-12T00:05:00Z"
    assert isinstance(run.target, WebWidgetTarget)
    sample = run.samples[0]
    assert sample.steps_run == 1
    assert sample.steps_total == 1
    result = sample.step_results[0]
    assert result.step_id == "s1"
    assert result.action_type == "expect"
    assert result.action_value == "hello"
    assert result.expected_transcript == "Hello there"
    assert result.actual_transcript == "Hello there"
    assert result.duration == 0.42


def test_run_requires_the_documented_required_fields():
    # `required: [id, workspaceId, targetRef, channel, kind, status, startedAt]`
    with pytest.raises(ValidationError):
        DigitalTestRun.model_validate(
            {"id": "r1", "workspaceId": "w1", "targetRef": "acme/billing-bot"}
        )


def test_run_pass_rate_tolerates_null_before_a_verdict():
    run = DigitalTestRun.model_validate(
        {
            "id": "r1",
            "workspaceId": "w1",
            "targetRef": "acme/billing-bot",
            "channel": "chat",
            "kind": "compliance",
            "status": "running",
            "startedAt": "2026-08-12T00:00:00Z",
            "passRate": None,
        }
    )
    assert run.pass_rate is None


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


def test_create_run_request_serialises_to_camel_case():
    req = CreateDigitalTestRunRequest(
        target_ref="acme/billing-bot",
        target=WebWidgetTarget(url="https://example.com/support"),
        sector="utilities",
        mission="Pay my bill",
        kind="freeform",
        acceptance="The bot states the balance",
        catalogue_test_id="M-001",
        pass_conditions=["states the balance"],
        fail_conditions=["asks for a password"],
        additional_context="Customer is in arrears",
        profile_id="p1",
        profile_snapshot={"accountNumber": "12345678"},
        probes=["what do I owe?"],
        samples=3,
        max_turns=12,
    )
    body = req.model_dump(by_alias=True, exclude_none=True)
    assert body["targetRef"] == "acme/billing-bot"
    assert body["target"] == {"transport": "web-widget", "url": "https://example.com/support"}
    assert body["catalogueTestId"] == "M-001"
    assert body["passConditions"] == ["states the balance"]
    assert body["failConditions"] == ["asks for a password"]
    assert body["additionalContext"] == "Customer is in arrears"
    assert body["profileId"] == "p1"
    assert body["profileSnapshot"] == {"accountNumber": "12345678"}
    assert body["maxTurns"] == 12
    # Standalone schema in the document: no name/description on the run request.
    assert "name" not in body
    assert "description" not in body


def test_create_run_request_requires_target_ref_target_sector_mission():
    with pytest.raises(ValidationError):
        CreateDigitalTestRunRequest.model_validate(
            {"targetRef": "acme/billing-bot", "sector": "utilities"}
        )


def test_create_run_request_carries_standard_steps():
    req = CreateDigitalTestRunRequest.model_validate(
        {
            "targetRef": "acme/billing-bot",
            "target": {"transport": "http-json", "endpoint": "https://bot.example.com/v1/chat"},
            "sector": "utilities",
            "mission": "Pay my bill",
            "kind": "standard",
            "steps": [
                {"type": "send", "profileItemId": "accountNumber"},
                {"type": "expect", "expected": "Thanks", "matcher": "contains"},
                {"type": "end"},
            ],
        }
    )
    assert [type(s) for s in req.steps] == [SendChatStep, ExpectChatStep, EndChatStep]
    assert req.model_dump(by_alias=True, exclude_none=True)["steps"][0] == {
        "type": "send",
        "profileItemId": "accountNumber",
    }


def test_create_config_request_requires_name_as_well():
    with pytest.raises(ValidationError):
        CreateDigitalTestConfigRequest.model_validate(
            {
                "targetRef": "acme/billing-bot",
                "target": {"transport": "web-widget", "url": "https://example.com/support"},
                "sector": "utilities",
                "mission": "Pay my bill",
            }
        )

    req = CreateDigitalTestConfigRequest.model_validate(
        {
            "name": "Billing bot smoke",
            "description": "Nightly",
            "targetRef": "acme/billing-bot",
            "target": {"transport": "web-widget", "url": "https://example.com/support"},
            "sector": "utilities",
            "mission": "Pay my bill",
        }
    )
    assert req.name == "Billing bot smoke"
    assert req.description == "Nightly"


def test_update_config_request_is_fully_optional():
    req = UpdateDigitalTestConfigRequest.model_validate({"mission": "Check my balance"})
    assert req.model_dump(by_alias=True, exclude_none=True) == {"mission": "Check my balance"}


def test_launch_request_overrides_only():
    req = LaunchDigitalTestConfigRequest.model_validate(
        {
            "targetRef": "acme/other-bot",
            "target": {"transport": "http-json", "endpoint": "https://other.example.com/chat"},
            "samples": 5,
        }
    )
    assert req.target_ref == "acme/other-bot"
    assert isinstance(req.target, HttpJsonTarget)
    assert req.samples == 5


# ---------------------------------------------------------------------------
# Configs and envelopes
# ---------------------------------------------------------------------------


def test_config_parses_server_set_fields():
    cfg = DigitalTestConfig.model_validate(
        {
            "id": "3f0a1a2e-0000-4000-8000-000000000002",
            "workspaceId": "w1",
            "userId": "u1",
            "name": "Billing bot smoke",
            "targetRef": "acme/billing-bot",
            "target": {"transport": "web-widget", "url": "https://example.com/support"},
            "sector": "utilities",
            "mission": "Pay my bill",
            "kind": "freeform",
            "createdAt": "2026-08-12T00:00:00Z",
            "updatedAt": "2026-08-12T00:00:01Z",
        }
    )
    assert cfg.workspace_id == "w1"
    assert cfg.user_id == "u1"
    assert cfg.created_at == "2026-08-12T00:00:00Z"
    assert cfg.updated_at == "2026-08-12T00:00:01Z"


def test_config_requires_the_server_set_fields():
    with pytest.raises(ValidationError):
        DigitalTestConfig.model_validate(
            {
                "name": "Billing bot smoke",
                "targetRef": "acme/billing-bot",
                "target": {"transport": "web-widget", "url": "https://example.com/support"},
                "sector": "utilities",
                "mission": "Pay my bill",
                "kind": "freeform",
            }
        )


def test_create_run_response_envelope():
    res = CreateDigitalTestRunResponse.model_validate(
        {
            "message": "Digital test queued",
            "run": {
                "id": "r1",
                "workspaceId": "w1",
                "targetRef": "acme/billing-bot",
                "channel": "chat",
                "kind": "freeform",
                "status": "pending",
                "startedAt": "2026-08-12T00:00:00Z",
            },
        }
    )
    assert res.message == "Digital test queued"
    assert res.run.id == "r1"


def test_list_runs_response_omits_next_cursor_on_the_last_page():
    res = ListDigitalTestRunsResponse.model_validate(
        {
            "runs": [
                {
                    "id": "r1",
                    "workspaceId": "w1",
                    "targetRef": "acme/billing-bot",
                    "channel": "chat",
                    "kind": "freeform",
                    "status": "completed",
                    "startedAt": "2026-08-12T00:00:00Z",
                }
            ]
        }
    )
    assert res.next_cursor is None
    assert len(res.runs) == 1

    paged = ListDigitalTestRunsResponse.model_validate({"runs": [], "nextCursor": "eyJrIjoxfQ=="})
    assert paged.next_cursor == "eyJrIjoxfQ=="


def test_list_configs_response():
    res = ListDigitalTestConfigsResponse.model_validate(
        {
            "configs": [
                {
                    "id": "c1",
                    "workspaceId": "w1",
                    "name": "Billing bot smoke",
                    "targetRef": "acme/billing-bot",
                    "target": {"transport": "web-widget", "url": "https://example.com/support"},
                    "sector": "utilities",
                    "mission": "Pay my bill",
                    "kind": "freeform",
                    "createdAt": "2026-08-12T00:00:00Z",
                    "updatedAt": "2026-08-12T00:00:01Z",
                }
            ],
            "nextCursor": "eyJrIjoyfQ==",
        }
    )
    assert res.configs[0].target_ref == "acme/billing-bot"
    assert res.next_cursor == "eyJrIjoyfQ=="


def test_compliance_audits_response():
    res = ListDigitalComplianceAuditsResponse.model_validate(
        {
            "audits": [
                {
                    "targetRef": "acme/billing-bot",
                    "lastRunAt": "2026-08-12T00:00:00Z",
                    "runCount": 4,
                    "catalogueTestIds": ["M-001", "M-002"],
                }
            ]
        }
    )
    audit = res.audits[0]
    assert audit.target_ref == "acme/billing-bot"
    assert audit.last_run_at == "2026-08-12T00:00:00Z"
    assert audit.run_count == 4
    assert audit.catalogue_test_ids == ["M-001", "M-002"]


def test_compliance_audit_summary_requires_all_four_fields():
    with pytest.raises(ValidationError):
        ListDigitalComplianceAuditsResponse.model_validate(
            {"audits": [{"targetRef": "acme/billing-bot"}]}
        )


# ---------------------------------------------------------------------------
# Voices (GET /testing/voices — tagged under Mission Tests)
# ---------------------------------------------------------------------------


def test_voice_uses_voice_id_not_id():
    v = Voice.model_validate(
        {
            "voiceId": "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae",
            "name": "Alistair",
            "language": "en-GB",
            "accent": "British",
            "gender": "male",
            "provider": "telnyx",
            "label": "Warm British male voice.",
            "isDefault": True,
        }
    )
    assert v.voice_id == "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae"
    assert v.name == "Alistair"
    assert v.language == "en-GB"
    assert v.accent == "British"
    assert v.gender == "male"
    assert v.provider == "telnyx"
    assert v.label == "Warm British male voice."
    assert v.is_default is True


def test_voice_requires_voice_id_and_name():
    with pytest.raises(ValidationError):
        Voice.model_validate({"name": "Alistair"})
    with pytest.raises(ValidationError):
        Voice.model_validate({"voiceId": "Telnyx.Ultra.abc"})


def test_list_voices_response():
    res = ListVoicesResponse.model_validate(
        {
            "voices": [
                {"voiceId": "Telnyx.Ultra.abc", "name": "Alistair", "isDefault": True},
                {"voiceId": "Telnyx.Ultra.def", "name": "Bea"},
            ],
            "defaultVoiceId": "Telnyx.Ultra.abc",
        }
    )
    assert res.default_voice_id == "Telnyx.Ultra.abc"
    assert [v.voice_id for v in res.voices] == ["Telnyx.Ultra.abc", "Telnyx.Ultra.def"]


def test_list_voices_response_tolerates_no_default():
    res = ListVoicesResponse.model_validate(
        {"voices": [{"voiceId": "Telnyx.Ultra.abc", "name": "Alistair"}]}
    )
    assert res.default_voice_id is None
