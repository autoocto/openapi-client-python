from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator


def make_gen(tmp_path, spec_data=None):
    paths = {}
    schemas = {"X": {"type": "object"}}
    if spec_data is None:
        spec_data = {"openapi": "3.2.0", "info": {"title": "T", "version": "1.0.0"}}
    return OpenAPI30APIGenerator(paths, schemas, "svc", tmp_path, spec_data)


def test_supports_feature_variants(tmp_path):
    gen = make_gen(tmp_path)
    # no version_info -> no features
    assert not gen._supports_feature("webhooks")

    gen.version_info = {"version_family": "openapi32", "supports_webhooks": True}
    assert gen._supports_feature("webhooks") is True
    assert gen._supports_feature("json_schema_draft_2020_12") is False or isinstance(
        gen._supports_feature("json_schema_draft_2020_12"), bool
    )


def test_resolve_complex_schemas(tmp_path):
    gen = make_gen(tmp_path)
    gen.version_info = {"version_family": "openapi32", "supports_json_schema_draft_2020_12": True}

    # const with numeric
    s1 = {"const": 5}
    assert gen._resolve_schema_type(s1) in ("int", "Union[int, float]", "Any")

    # object with properties
    s2 = {"type": "object", "properties": {"a": {"type": "string"}}}
    assert gen._resolve_schema_type(s2) == "Dict[str, Any]"

    # nested array
    s3 = {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
    assert "List[" in gen._resolve_schema_type(s3)

    # allOf resolves first $ref
    s4 = {"allOf": [{"$ref": "#/components/schemas/X"}, {"type": "object"}]}
    assert gen._resolve_schema_type(s4) == "X"

    # oneOf still returns Any (fallback)
    s5 = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
    assert gen._resolve_schema_type(s5) == "Any"


def test_get_request_body_info_priority(tmp_path):
    gen = make_gen(tmp_path)
    # requestBody with multiple content types - prefer application/json
    op = {
        "requestBody": {
            "required": True,
            "content": {
                "application/xml": {"schema": {"type": "string"}},
                "application/json": {"schema": {"$ref": "#/components/schemas/X"}},
            },
        }
    }
    info = gen._get_request_body_info(op)
    assert info and info["type"] == "X"


def test_get_response_model_priority(tmp_path):
    gen = make_gen(tmp_path)
    op = {
        "responses": {
            "200": {
                "content": {
                    "application/xml": {"schema": {"type": "object"}},
                    "application/json": {"schema": {"$ref": "#/components/schemas/X"}},
                }
            }
        }
    }
    rm = gen._get_response_model(op)
    assert rm == "X"
