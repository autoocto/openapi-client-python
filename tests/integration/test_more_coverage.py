"""
Additional tests for API generator to achieve full coverage.
"""

import json
from openapi_client_generator.api_generator import APIGenerator
from openapi_client_generator.spec_loader import SpecLoader
from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator


def test_api_generator_wrapper_types(tmp_path):
    paths = {}
    schemas = {}
    # OpenAPI 3.x
    out_dir = tmp_path / "out1"
    out_dir.mkdir()
    gen3 = APIGenerator(paths, schemas, "svc", out_dir, True)
    assert hasattr(gen3, "generator")

    # Swagger 2.0
    out_dir2 = tmp_path / "out2"
    out_dir2.mkdir()
    gen2 = APIGenerator(paths, schemas, "svc", out_dir2, False)
    assert hasattr(gen2, "generator")


def test_spec_loader_swagger_and_openapi(tmp_path):
    # swagger 2.0 spec with host/basePath/schemes
    swagger = {
        "swagger": "2.0",
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "paths": {},
        "info": {"title": "S", "version": "1.0.0"},
        "definitions": {"A": {"type": "object"}},
    }
    f1 = tmp_path / "swagger.json"
    f1.write_text(json.dumps(swagger))

    sl = SpecLoader(str(f1))
    servers = sl.get_servers()
    assert servers and servers[0]["url"].startswith("https://api.example.com")
    assert sl.get_base_path() == "/v1"

    # openapi 3.1 spec
    openapi31 = {
        "openapi": "3.1.0",
        "info": {"title": "O", "version": "1.0.0"},
        "servers": [{"url": "https://api2.example.com"}],
        "paths": {},
        "components": {"schemas": {"B": {"type": "object"}}},
    }
    f2 = tmp_path / "openapi31.json"
    f2.write_text(json.dumps(openapi31))

    sl2 = SpecLoader(str(f2))
    vi = sl2.get_version_info()
    assert vi.get("version_family") in ("openapi31", "openapi3", "openapi32")
    assert sl2.get_servers()[0]["url"] == "https://api2.example.com"


def test_openapi30_resolve_schema_and_features(tmp_path):
    paths = {}
    schemas = {"User": {"type": "object"}}
    spec_data = {"openapi": "3.1.0", "info": {"title": "T", "version": "1.0.0"}}
    gen = OpenAPI30APIGenerator(paths, schemas, "svc", tmp_path, spec_data)

    # Simulate version_info enabling features
    gen.version_info = {"version_family": "openapi31", "supports_json_schema_draft_2020_12": True}
    assert gen._supports_feature("json_schema_draft_2020_12") is True

    # $ref resolution
    ref_schema = {"$ref": "#/components/schemas/User"}
    assert gen._resolve_schema_type(ref_schema) == "User"

    # const handling when feature enabled
    const_schema = {"const": "abc"}
    assert gen._resolve_schema_type(const_schema) == "str"

    # array handling
    arr = {"type": "array", "items": {"type": "string"}}
    assert gen._resolve_schema_type(arr).startswith("List[")

    # oneOf / anyOf (falls back to Any)
    union_schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
    assert gen._resolve_schema_type(union_schema) == "Any"

    # allOf with $ref inside
    allof_schema = {"allOf": [{"$ref": "#/components/schemas/User"}, {"type": "object"}]}
    assert gen._resolve_schema_type(allof_schema) == "User"

    # get_content_types with requestBody and response content
    op = {
        "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
        "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}},
    }
    consumes, produces = gen._get_content_types(op)
    assert "application/json" in consumes
    assert "application/json" in produces
