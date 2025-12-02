from openapi_client_generator.base_api_generator import BaseAPIGenerator


def test_generate_method_with_list_model(tmp_path):
    class SubGen(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return {"type": "List[User]", "required": True, "is_json": True}

        def _get_response_model(self, operation):
            return "List[User]"

        def _get_content_types(self, operation):
            return (["application/json"], ["application/json"])

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

    gen = SubGen(paths, {"User": {}}, "svc", tmp_path)
    content = gen._generate_apis_content("SvcAPIs", gen._extract_operations())

    # method signature and path param name transformed to snake_case
    assert "def create_item(" in content
    assert "{item_id}" in content or "{item_id}" in content

    # params handling and headers present
    assert "params = {}" in content
    assert "headers = self.get_headers()" in content

    # list model handling
    assert "return [User.from_dict(item) for item in response.json()]" in content


def test_generate_method_primitive_and_raw_responses(tmp_path):
    class SubGenStr(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return "str"

        def _get_content_types(self, operation):
            return ([], [])

    class SubGenRaw(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

    paths = {"/p": {"get": {"operationId": "ping", "parameters": [], "responses": {"200": {}}}}}

    gen_str = SubGenStr(paths, {}, "svc", tmp_path)
    content_str = gen_str._generate_apis_content("SvcAPIs", gen_str._extract_operations())
    assert "return response.text" in content_str

    gen_raw = SubGenRaw(paths, {}, "svc", tmp_path)
    content_raw = gen_raw._generate_apis_content("SvcAPIs", gen_raw._extract_operations())
    assert "return self._make_request(" in content_raw


def test_generate_imports_includes_model_imports(tmp_path):
    class SubGen(BaseAPIGenerator):
        def _get_request_body_info(self, operation):
            return None

        def _get_response_model(self, operation):
            return None

        def _get_content_types(self, operation):
            return ([], [])

    gen = SubGen({}, {"User": {}}, "svc", tmp_path)
    imports = gen._generate_imports()
    assert "from .models.User import User" in imports
