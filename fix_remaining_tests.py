import re

# Fix test_edge_cases.py
with open('tests/test_edge_cases.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all APIGenerator calls that use True with OpenAPI30APIGenerator
pattern1 = r'generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*True\s*\)'
replacement1 = r'spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}\n        generator = OpenAPI30APIGenerator(\1, \2, \3, \4, spec_data)'
content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)

# Replace all APIGenerator calls that use False with Swagger20APIGenerator  
pattern2 = r'generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*False\s*\)'
replacement2 = r'spec_data = {"swagger": "2.0", "info": {"title": "Test API", "version": "1.0.0"}}\n        generator = Swagger20APIGenerator(\1, \2, \3, \4, spec_data)'
content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)

with open('tests/test_edge_cases.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_edge_cases.py")

# Fix test_api_generator_coverage.py for method calls
with open('tests/test_api_generator_coverage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _get_request_body_model calls with _get_request_body_info
content = content.replace('_get_request_body_model(', '_get_request_body_info(')

# Fix the test assertions for request body model
content = content.replace(
    'assert request_model == \'User\'',
    'assert request_info and request_info.get(\'model\') == \'User\''
)
content = content.replace(
    'assert request_model == \'List[User]\'',
    'assert request_info and request_info.get(\'model\') == \'List[User]\''
)

with open('tests/test_api_generator_coverage.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_api_generator_coverage.py")