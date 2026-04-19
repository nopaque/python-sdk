"""Live smoke tests against https://api.dev.nopaque.co.uk.

Run with:
    NOPAQUE_API_KEY=... \
    NOPAQUE_BASE_URL=https://api.dev.nopaque.co.uk \
    hatch run test:integration

These are intentionally minimal - enough to detect a breaking server change
without costing real resources. They run nightly via
.github/workflows/nightly-integration.yml.
"""
import os

import pytest

from nopaque import Nopaque

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    if not os.environ.get("NOPAQUE_API_KEY"):
        pytest.skip("NOPAQUE_API_KEY not set")
    c = Nopaque()
    yield c
    c.close()


def test_list_profiles(client):
    # Read-only: should always succeed without modifying anything.
    seen = 0
    for _p in client.profiles.list(limit=5):
        seen += 1
    assert seen >= 0  # 0 is fine - just verifies the call returns


def test_create_get_delete_schedule(client):
    # Create -> get -> delete a throwaway schedule.
    sched = client.scheduler.create(
        name="sdk-smoke-test",
        config_id=os.environ.get("NOPAQUE_SMOKE_CONFIG_ID", "cfg_placeholder"),
        cron_expression="0 0 * * *",
    )
    try:
        got = client.scheduler.get(sched.id)
        assert got.id == sched.id
    finally:
        client.scheduler.delete(sched.id)


def test_create_audio_upload_url(client):
    # Exercises the presign call without actually uploading a file.
    res = client.audio.create_upload_url(
        file_name="smoke-test.wav",
        content_type="audio/wav",
    )
    assert res.upload_url.startswith("https://")
    assert res.audio_id
