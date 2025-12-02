# small extra integration tests
from openapi_client_generator.base_api_generator import BaseAPIGenerator


def test_call_abstract_methods_do_nothing():
    # ensure the abstract methods can be invoked without side effects
    BaseAPIGenerator._get_request_body_info(object(), {})
    BaseAPIGenerator._get_response_model(object(), {})
    BaseAPIGenerator._get_content_types(object(), {})


def test_dummy():
    assert True
