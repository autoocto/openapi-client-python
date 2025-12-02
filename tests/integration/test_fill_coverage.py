import json
import pytest

from openapi_client_generator.spec_loader import SpecLoader
from openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator
from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator
from openapi_client_generator.base_api_generator import BaseAPIGenerator


def test_spec_loader_version_errors_and_normalization(tmp_path):
    # missing keys -> Invalid spec
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({}))
    with pytest.raises(ValueError):
        SpecLoader(str(f))

    # openapi short form '3.0' should normalize to 3.0.0
    f2 = tmp_path / "o3.json"
    f2.write_text(json.dumps({"openapi": "3.0", "info": {"title": "T", "version": "1.0.0"}}))
    s = SpecLoader(str(f2))
    vi = s.get_version_info()
    assert vi["version_family"].startswith("openapi")

    # unsupported version -> error
    f3 = tmp_path / "o4.json"
    f3.write_text(json.dumps({"openapi": "4.0.0", "info": {"title": "T", "version": "1.0.0"}}))
    with pytest.raises(ValueError):
        SpecLoader(str(f3))


def test_swagger20_request_body_and_response_variants(tmp_path):
    paths = {}
    schemas = {"U": {"type": "object"}}
    spec = {
        "swagger": "2.0",
        "host": "h",
        "basePath": "/",
        "schemes": ["https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
    }
    gen = Swagger20APIGenerator(paths, schemas, "svc", tmp_path, spec)

    # body param with external $ref -> Any
    op = {
        "parameters": [
            {"in": "body", "required": True, "schema": {"$ref": "http://example.com/defs/U"}}
        ],
        "responses": {},
    }
    info = gen._get_request_body_info(op)
    assert info and info["type"] == "Any"

    # array items with external ref -> List[Any]
    op2 = {
        "parameters": [
            {
                "in": "body",
                "required": True,
                "schema": {"type": "array", "items": {"$ref": "http://other/defs/U"}},
            }
        ],
        "responses": {
            "200": {"schema": {"type": "array", "items": {"$ref": "http://other/defs/U"}}}
        },
    }
    info2 = gen._get_request_body_info(op2)
    assert info2 and "List" in info2["type"]

    # response model with external ref -> None
    resp = gen._get_response_model({"responses": {"200": {"schema": {"$ref": "http://x"}}}})
    assert resp is None

    # content types from spec_data used when operation lacks them
    consumes, produces = gen._get_content_types({})
    assert consumes == spec["consumes"]
    assert produces == spec["produces"]


def test_openapi30_unusual_refs_and_parameters(tmp_path):
    gen = OpenAPI30APIGenerator(
        {}, {}, "svc", tmp_path, {"openapi": "3.0.0", "info": {"title": "t", "version": "1.0.0"}}
    )
    # $ref not in components -> Any
    assert gen._resolve_schema_type({"$ref": "#/somewhere/Else"}) == "Any"

    # const with float
    gen.version_info = {"version_family": "openapi31", "supports_json_schema_draft_2020_12": True}
    assert gen._resolve_schema_type({"const": 3.14}) in ("Union[int, float]", "Any")

    # parameter with no type -> defaults
    assert gen._get_parameter_type({}) == gen._resolve_schema_type({})


def test_base_find_body_parameter():
    class Dummy(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

    # use the tmp_path fixture as the output directory
    import pathlib

    out_dir = pathlib.Path(".")
    d = Dummy({}, {}, "s", out_dir)
    # no body
    assert d._find_body_parameter([]) is None
    # with body
    param = {"name": "body", "in": "body", "schema": {"type": "object"}}
    assert d._find_body_parameter([param]) == param


def test_call_abstract_methods_do_nothing():
    # ensure the abstract methods can be invoked without side effects
    from openapi_client_generator.base_api_generator import BaseAPIGenerator as _B

    # call the abstract methods with dummy args
    _B._get_request_body_info(object(), {})
    _B._get_response_model(object(), {})
    _B._get_content_types(object(), {})


def test_api_generator_wrapper_types(tmp_path):
    # small integration checks for APIGenerator wrapper types
    from openapi_client_generator.api_generator import APIGenerator

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
    # combined checks covering Swagger 2.0 and OpenAPI 3.1 handling
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
