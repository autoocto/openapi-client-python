import re

def fix_file(filename):
    # Read the file
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace imports
    content = content.replace(
        'from openapi_client_generator.api_generator import APIGenerator',
        'from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator\nfrom openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator'
    )

    # Replace all APIGenerator calls that use 'True' with OpenAPI30APIGenerator
    pattern1 = r'generator = APIGenerator\(([^,]+), ([^,]+), ([^,]+), ([^,]+), True\)'
    replacement1 = r'spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}\n        generator = OpenAPI30APIGenerator(\1, \2, \3, \4, spec_data)'
    content = re.sub(pattern1, replacement1, content)

    # Replace all APIGenerator calls that use 'False' with Swagger20APIGenerator  
    pattern2 = r'generator = APIGenerator\(([^,]+), ([^,]+), ([^,]+), ([^,]+), False\)'
    replacement2 = r'spec_data = {"swagger": "2.0", "info": {"title": "Test API", "version": "1.0.0"}}\n        generator = Swagger20APIGenerator(\1, \2, \3, \4, spec_data)'
    content = re.sub(pattern2, replacement2, content)

    # Write back
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Fixed all APIGenerator references in {filename}')

# Fix both files
fix_file('tests/test_api_generator_coverage.py')
fix_file('tests/test_edge_cases.py')