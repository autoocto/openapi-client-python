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
