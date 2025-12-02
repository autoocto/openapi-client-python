"""Unit tests for base_api_generator module."""

from pathlib import Path

from openapi_client_generator.base_api_generator import BaseAPIGenerator


def _make_dummy(sub_overrides=None):
    """Helper to create a minimal concrete subclass with optional overrides."""

    class Dummy(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

    if sub_overrides:
        for name, fn in sub_overrides.items():
            setattr(Dummy, name, fn)

    return Dummy


def test_call_abstract_methods_pass_lines():
    """Test that abstract methods can be called directly."""
    BaseAPIGenerator._get_request_body_info(object(), {})
    BaseAPIGenerator._get_response_model(object(), {})
    BaseAPIGenerator._get_content_types(object(), {})


def test_generate_method_name_from_path_and_operation(tmp_path):
    """Test generating method name from path and operation."""
    Dummy = _make_dummy()
    paths = {"/a/b/{id}": {"get": {"parameters": [], "responses": {"200": {}}}}}
    gen = Dummy(paths, {}, "svc", tmp_path)
    ops = gen._extract_operations()
    content = gen._generate_apis_content("SvcAPIs", ops)
    assert "def get_a_b(" in content or "def get_a_b_" in content


def test_single_part_path_method_name_and_signature(tmp_path):
    """Test method name generation for single-part paths."""
    Dummy = _make_dummy()
    paths = {"/items": {"get": {"parameters": [], "responses": {"200": {}}}}}
    d = Dummy(paths, {}, "svc", tmp_path)
    content = d._generate_apis_content("SvcAPIs", d._extract_operations())
    assert "def get_items(" in content or "def get_items" in content


def test_get_parameter_type_array_branch(tmp_path):
    """Test parameter type handling for arrays."""
    Dummy = _make_dummy()
    d = Dummy({}, {}, "svc", tmp_path)
    param = {"type": "array", "items": {"type": "integer", "format": "int32"}}
    t = d._get_parameter_type(param)
    assert t == "List[int]"


def test_multi_part_path_method_name(tmp_path):
    """Test method name generation for multi-part paths."""
    Dummy = _make_dummy()
    paths = {"/a/b/c": {"get": {"parameters": [], "responses": {"200": {}}}}}
    d = Dummy(paths, {}, "svc", tmp_path)
    content = d._generate_apis_content("SvcAPIs", d._extract_operations())
    assert "def get_a_b_c(" in content or "def get_a_b_c" in content


def test_generate_method_name_direct_multi_part_branch():
    """Test direct method name generation for multi-part paths."""
    Dummy = _make_dummy()
    d = Dummy({}, {}, "svc", Path("."))
    op = {"operation_id": "", "path": "/one/two/three", "method": "GET"}
    name = d._generate_method_name(op)
    assert "get_one_two_three" in name


def test_parameter_and_cookie_and_header_and_query_handling(tmp_path):
    """Test handling of path, query, header and cookie parameters."""

    def rb(self, operation):
        return {"type": "List[User]", "required": True, "is_json": True}

    def resp(self, operation):
        return "List[User]"

    def content_types(self, operation):
        return (["application/json"], ["application/json"])

    Dummy = _make_dummy(
        {
            "_get_request_body_info": rb,
            "_get_response_model": resp,
            "_get_content_types": content_types,
        }
    )

    paths = {
        "/v1/items/{itemId}": {
            "post": {
                "operationId": "createItem",
                "parameters": [
                    {
                        "name": "itemId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}},
                    {
                        "name": "X-API",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "sess",
                        "in": "cookie",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                ],
                "responses": {"200": {"description": "OK"}},
            }
        }
    }

    gen = Dummy(paths, {"User": {}}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())

    assert "def create_item(" in content
    assert "{item_id}" in content
    assert "params = {}" in content
    assert "headers = self.get_headers()" in content
    assert "cookies = {}" in content
    assert 'cookies["sess"]' in content
    assert "return [User.from_dict(item) for item in response.json()]" in content


def test_imports_and_model_handling(tmp_path):
    """Test model imports generation."""
    Dummy = _make_dummy()
    gen = Dummy({}, {"User": {}}, "svc", tmp_path)
    imports = gen._generate_imports()
    assert "from .models.User import User" in imports


def test_primitive_and_raw_responses(tmp_path):
    """Test handling of primitive and raw response types."""

    def resp_text(self, operation):
        return "str"

    def resp_none(self, operation):
        return None

    SubText = _make_dummy({"_get_response_model": resp_text})
    SubRaw = _make_dummy({"_get_response_model": resp_none})

    paths_text = {
        "/p": {"get": {"operationId": "ping", "parameters": [], "responses": {"200": {}}}}
    }

    gen_text = SubText(paths_text, {}, "svc", tmp_path)
    content_text = gen_text._generate_apis_content("SvcAPIs", gen_text._extract_operations())
    assert "return response.text" in content_text or "return response.json()" in content_text

    gen_raw = SubRaw(paths_text, {}, "svc", tmp_path)
    content_raw = gen_raw._generate_apis_content("SvcAPIs", gen_raw._extract_operations())
    assert "return self._make_request(" in content_raw


def test_single_model_response_and_optional_body(tmp_path):
    """Test handling of single model responses and optional request bodies."""

    def rb(self, operation):
        return {"type": "User", "required": False, "is_json": True}

    def resp(self, operation):
        return "User"

    Dummy = _make_dummy({"_get_request_body_info": rb, "_get_response_model": resp})
    paths = {
        "/u/{id}": {
            "put": {
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {}},
            }
        }
    }
    gen = Dummy(paths, {"User": {}}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())
    assert "payload: User = None" in content
    assert "return User.from_dict(response.json())" in content


def test_primitive_responses_int_and_bool(tmp_path):
    """Test handling of primitive int and bool responses."""

    def resp_int(self, operation):
        return "int"

    def resp_bool(self, operation):
        return "bool"

    SubInt = _make_dummy({"_get_response_model": resp_int})
    SubBool = _make_dummy({"_get_response_model": resp_bool})
    paths = {"/n": {"get": {"parameters": [], "responses": {"200": {}}}}}
    g1 = SubInt(paths, {}, "svc", tmp_path)
    c1 = g1._generate_apis_content("SvcAPIs", g1._extract_operations())
    assert "return response.json()" in c1

    g2 = SubBool(paths, {}, "svc", tmp_path)
    c2 = g2._generate_apis_content("SvcAPIs", g2._extract_operations())
    assert "return response.json()" in c2


def test_cookie_handling_required_and_optional(tmp_path):
    """Test cookie parameter handling for both required and optional cookies."""
    Dummy = _make_dummy()
    paths = {
        "/c": {
            "get": {
                "parameters": [
                    {"name": "sid", "in": "cookie", "required": True, "schema": {"type": "string"}},
                    {
                        "name": "opt",
                        "in": "cookie",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                ],
                "responses": {"200": {}},
            }
        }
    }

    gen = Dummy(paths, {}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())
    assert "cookies = {}" in content
    assert 'cookies["sid"] = sid' in content
    assert "if opt is not None:" in content
