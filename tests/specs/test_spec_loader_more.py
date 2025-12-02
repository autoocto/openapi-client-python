import json
import pytest

from openapi_client_generator.spec_loader import SpecLoader


def write_spec(tmp_path, data, name="spec.json"):
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def test_invalid_spec_missing_keys(tmp_path):
    # Empty spec should raise
    p = write_spec(tmp_path, {})
    with pytest.raises(ValueError):
        SpecLoader(p)


def test_openapi_version_normalization_and_family(tmp_path):
    # short form '3.0' should normalize to 3.0.0 and map to openapi3
    spec = {"openapi": "3.0", "info": {"title": "t", "version": "1.0.0"}}
    p = write_spec(tmp_path, spec, "o30.json")
    s = SpecLoader(p)
    vi = s.get_version_info()
    assert vi["version_family"].startswith("openapi")

    # 3.2.x should default to openapi32
    spec2 = {"openapi": "3.2.1", "info": {"title": "t", "version": "1.0.0"}}
    p2 = write_spec(tmp_path, spec2, "o321.json")
    s2 = SpecLoader(p2)
    assert s2.get_version_info()["version_family"] == "openapi32"


def test_openapi_unsupported_version(tmp_path):
    spec = {"openapi": "4.0.0", "info": {"title": "t", "version": "1.0.0"}}
    p = write_spec(tmp_path, spec, "bad.json")
    with pytest.raises(ValueError):
        SpecLoader(p)


def test_swagger_non_2_0_raises(tmp_path):
    spec = {"swagger": "1.0", "info": {"title": "t", "version": "1.0.0"}}
    p = write_spec(tmp_path, spec, "s1.json")
    with pytest.raises(ValueError):
        SpecLoader(p)


def test_get_schemas_components_and_definitions(tmp_path):
    openapi = {
        "openapi": "3.0.0",
        "info": {"title": "t", "version": "1.0.0"},
        "components": {"schemas": {"A": {}}},
    }
    p1 = write_spec(tmp_path, openapi, "oa.json")
    s1 = SpecLoader(p1)
    assert "A" in s1.get_schemas()

    swagger = {
        "swagger": "2.0",
        "info": {"title": "t", "version": "1.0.0"},
        "definitions": {"B": {}},
    }
    p2 = write_spec(tmp_path, swagger, "sw.json")
    s2 = SpecLoader(p2)
    assert "B" in s2.get_schemas()


def test_get_servers_and_base_path(tmp_path):
    # swagger host -> servers conversion
    swagger = {
        "swagger": "2.0",
        "host": "api.test",
        "basePath": "/v1",
        "schemes": ["http"],
        "info": {"title": "t", "version": "1.0.0"},
    }
    p = write_spec(tmp_path, swagger, "sw2.json")
    s = SpecLoader(p)
    servers = s.get_servers()
    assert any(d.get("url") == "http://api.test/v1" for d in servers)
    assert s.get_base_path() == "/v1"

    # openapi servers returned as-is and base_path empty
    openapi = {
        "openapi": "3.0.0",
        "servers": [{"url": "https://x"}],
        "info": {"title": "t", "version": "1.0.0"},
    }
    p2 = write_spec(tmp_path, openapi, "oa2.json")
    s2 = SpecLoader(p2)
    assert s2.get_servers() == [{"url": "https://x"}]
    assert s2.get_base_path() == ""


def test_version_info_flags(tmp_path):
    o31 = {"openapi": "3.1.0", "info": {"title": "t", "version": "1.0.0"}}
    p = write_spec(tmp_path, o31, "o31.json")
    s = SpecLoader(p)
    vi = s.get_version_info()
    assert vi["supports_webhooks"] == "True"
    assert vi["supports_json_schema_draft_2020_12"] == "True"

    sw = {"swagger": "2.0", "info": {"title": "t", "version": "1.0.0"}}
    p2 = write_spec(tmp_path, sw, "sw22.json")
    s2 = SpecLoader(p2)
    vi2 = s2.get_version_info()
    assert vi2["is_swagger2"] == "True"
    assert vi2["supports_webhooks"] == "False"
