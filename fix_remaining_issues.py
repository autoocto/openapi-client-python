import re

# Fix the edge cases file more specifically
with open('tests/test_edge_cases.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for APIGenerator calls with is_openapi3=True
pattern1 = r'(\s*)generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*is_openapi3=True\s*\)'
replacement1 = r'\1spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}\n\1generator = OpenAPI30APIGenerator(\2, \3, \4, \5, spec_data)'
content = re.sub(pattern1, replacement1, content)

# Pattern for APIGenerator calls with is_openapi3=False
pattern2 = r'(\s*)generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*is_openapi3=False\s*\)'
replacement2 = r'\1spec_data = {"swagger": "2.0", "info": {"title": "Test API", "version": "1.0.0"}}\n\1generator = Swagger20APIGenerator(\2, \3, \4, \5, spec_data)'
content = re.sub(pattern2, replacement2, content)

with open('tests/test_edge_cases.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed edge cases file with parameter names")

# Also fix some variable name issues in coverage tests
with open('tests/test_api_generator_coverage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix undefined variable references
content = content.replace('request_model = generator._get_request_body_info', 'request_info = generator._get_request_body_info')
content = content.replace('assert request_model', 'assert request_info')

with open('tests/test_api_generator_coverage.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed variable name issues in coverage tests")