from nopaque._user_agent import compose_user_agent


def test_user_agent_format():
    ua = compose_user_agent()
    assert ua.startswith("nopaque-python/")
    assert "python/" in ua
    assert "httpx/" in ua


def test_user_agent_starts_with_sdk_name():
    ua = compose_user_agent()
    parts = ua.split(" ", 1)
    sdk_name_version = parts[0]
    assert "/" in sdk_name_version
    name, version = sdk_name_version.split("/")
    assert name == "nopaque-python"
    assert version
