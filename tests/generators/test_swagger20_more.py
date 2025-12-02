from pathlib import Path

from openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator


def make_gen(spec_data=None, schemas=None, paths=None, tmp_path=Path(".")):
    if spec_data is None:
        spec_data = {}
    if schemas is None:
        schemas = {}
    if paths is None:
        paths = {}
    return Swagger20APIGenerator(paths, schemas, "svc", tmp_path, spec_data)


def test_request_body_ref_and_array_variants(tmp_path):
    gen = make_gen(spec_data={}, schemas={"Pet": {}}, paths={}, tmp_path=tmp_path)

    # $ref to local definition should return model name
    op = {"parameters": [{"in": "body", "required": True, "schema": {"$ref": "#/definitions/Pet"}}]}
    info = gen._get_request_body_info(op)
    assert info is not None
    assert info["type"] == "Pet"

    # array with local $ref items -> List[Pet]
    op2 = {
        "parameters": [
            {
                "in": "body",
                "required": True,
                "schema": {"type": "array", "items": {"$ref": "#/definitions/Pet"}},
            }
        ]
    }
    info2 = gen._get_request_body_info(op2)
    assert info2 is not None
    assert info2["type"] == "List[Pet]"

    # array with external $ref items -> List[Any]
    op3 = {
        "parameters": [
            {
                "in": "body",
                "required": True,
                "schema": {"type": "array", "items": {"$ref": "http://example.com/defs/X"}},
            }
        ]
    }
    info3 = gen._get_request_body_info(op3)
    assert info3 is not None
    assert info3["type"] == "List[Any]"

    # simple primitive schema type
    op4 = {"parameters": [{"in": "body", "required": False, "schema": {"type": "string"}}]}
    info4 = gen._get_request_body_info(op4)
    assert info4 is not None
    assert info4["type"] == "str"


def test_response_model_selection_and_variants():
    gen = make_gen(spec_data={}, schemas={"Pet": {}}, tmp_path=Path("."))

    # response with string '200' and local $ref -> Pet
    op = {"responses": {"200": {"schema": {"$ref": "#/definitions/Pet"}}}}
    r = gen._get_response_model(op)
    assert r == "Pet"

    # response with integer 200 key and array of local refs -> List[Pet]
    op2 = {
        "responses": {200: {"schema": {"type": "array", "items": {"$ref": "#/definitions/Pet"}}}}
    }
    r2 = gen._get_response_model(op2)
    assert r2 == "List[Pet]"

    # response with array items external ref -> List[Any]
    op3 = {"responses": {"200": {"schema": {"type": "array", "items": {"$ref": "http://x/y"}}}}}
    r3 = gen._get_response_model(op3)
    assert r3 == "List[Any]"

    # simple primitive response
    op4 = {"responses": {"200": {"schema": {"type": "integer", "format": "int32"}}}}
    r4 = gen._get_response_model(op4)
    assert r4 == "int"

    # no success response -> None
    assert gen._get_response_model({"responses": {"400": {"description": "bad"}}}) is None


def test_parameter_type_file_and_array():
    gen = make_gen()

    p1 = {"name": "f", "in": "formData", "type": "file"}
    assert gen._get_parameter_type(p1) == "Any"

    p2 = {
        "name": "ids",
        "in": "query",
        "type": "array",
        "items": {"type": "integer", "format": "int32"},
    }
    assert gen._get_parameter_type(p2) == "List[int]"


def test_generate_init_default_url_from_spec():
    spec = {"host": "api.example.com", "basePath": "/v1", "schemes": ["https"]}
    gen = make_gen(spec_data=spec)
    init_code = gen._generate_init_method()
    assert "https://api.example.com/v1" in init_code
