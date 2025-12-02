from openapi_client_generator.base_api_generator import BaseAPIGenerator


def test_single_model_response_and_optional_body(tmp_path):
    class SubGen(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            # optional body
            return {"type": "User", "required": False, "is_json": True}

        def _get_response_model(self, operation):
            return "User"

        def _get_content_types(self, operation):
            return ([], [])

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
    gen = SubGen(paths, {"User": {}}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())

    # optional payload should set default to None in signature
    assert "payload: User = None" in content
    # single model response uses from_dict
    assert "return User.from_dict(response.json())" in content


def test_primitive_responses_int_and_bool(tmp_path):
    class SubInt(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return "int"

        def _get_content_types(self, operation):
            return ([], [])

    class SubBool(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return "bool"

        def _get_content_types(self, operation):
            return ([], [])

    paths = {"/n": {"get": {"parameters": [], "responses": {"200": {}}}}}
    g1 = SubInt(paths, {}, "svc", tmp_path)
    c1 = g1._generate_apis_content("SvcAPIs", g1._extract_operations())
    assert "return response.json()" in c1

    g2 = SubBool(paths, {}, "svc", tmp_path)
    c2 = g2._generate_apis_content("SvcAPIs", g2._extract_operations())
    assert "return response.json()" in c2


def test_cookie_handling_required_and_optional(tmp_path):
    class SubGen(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

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

    gen = SubGen(paths, {}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())

    # cookie dict should be created and both assignments present
    assert "cookies = {}" in content
    assert 'cookies["sid"] = sid' in content or 'cookies["sid"] = sid' in content
    assert "if opt is not None:" in content


def test_method_name_generation_from_path(tmp_path):
    class SubGen(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

    paths = {"/a/b/{id}": {"get": {"parameters": [], "responses": {"200": {}}}}}
    gen = SubGen(paths, {}, "svc", tmp_path)
    ops = gen._extract_operations()
    # generated method name should include both path parts
    content = gen._generate_apis_content("SvcAPIs", ops)
    assert "def get_a_b(" in content or "def get_a_b_" in content
