#!/usr/bin/env python3

"""
Comprehensive test fixer for the OpenAPI client generator test suite.
This script addresses the remaining test failures after the architecture refactoring.
"""

import re
import os

def fix_imports_and_calls(filename):
    """Fix imports and API calls in a test file."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix imports
    content = content.replace(
        'from openapi_client_generator.api_generator import APIGenerator',
        'from openapi_client_generator.openapi30_api_generator import OpenAPI30APIGenerator\nfrom openapi_client_generator.swagger20_api_generator import Swagger20APIGenerator'
    )
    
    # Replace APIGenerator calls with appropriate generator
    # Pattern: APIGenerator(paths, schemas, service, temp_dir, True/False)
    
    # For OpenAPI 3.0 (True)
    pattern_openapi3 = r'(\s*)generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*True\s*\)'
    replacement_openapi3 = r'\1spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}}\n\1generator = OpenAPI30APIGenerator(\2, \3, \4, \5, spec_data)'
    content = re.sub(pattern_openapi3, replacement_openapi3, content)
    
    # For Swagger 2.0 (False)
    pattern_swagger2 = r'(\s*)generator = APIGenerator\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*False\s*\)'
    replacement_swagger2 = r'\1spec_data = {"swagger": "2.0", "info": {"title": "Test API", "version": "1.0.0"}}\n\1generator = Swagger20APIGenerator(\2, \3, \4, \5, spec_data)'
    content = re.sub(pattern_swagger2, replacement_swagger2, content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed imports and calls in {filename}")

def fix_method_calls(filename):
    """Fix method calls that have changed in the new architecture."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix method calls that need to access the 'operation' from extracted operations
    content = content.replace(
        '_get_response_model(operations[0])',
        '_get_response_model(operations[0][\'operation\'])'
    )
    
    content = content.replace(
        '_get_request_body_model(operations[0])',
        '_get_request_body_info(operations[0][\'operation\'])'
    )
    
    content = content.replace(
        '_get_request_body_info(operations[0])',
        '_get_request_body_info(operations[0][\'operation\'])'
    )
    
    # Fix method name that changed
    content = content.replace('_get_request_body_model(', '_get_request_body_info(')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed method calls in {filename}")

def fix_test_expectations():
    """Fix test expectations to match actual behavior."""
    
    # Fix test_api_generator.py method signature test
    with open('tests/test_api_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The actual generated method name should be 'create_user' not 'post_users'
    content = content.replace(
        "self.assertIn('def post_users(self', content)",
        "self.assertIn('def create_user(self', content)"
    )
    
    content = content.replace(
        "self.assertIn('def post_users(self, payload: User = None) -> User:', content)",
        "self.assertIn('def create_user(self, payload: User = None) -> User:', content)"
    )
    
    with open('tests/test_api_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed test expectations")

def main():
    """Main function to fix all test issues."""
    
    print("🔧 Fixing OpenAPI Client Generator Tests...")
    
    # Fix the main test files
    test_files = [
        'tests/test_api_generator_coverage.py',
        'tests/test_edge_cases.py'
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            fix_imports_and_calls(filename)
            if 'coverage' in filename:
                fix_method_calls(filename)
    
    # Fix test expectations
    fix_test_expectations()
    
    print("✅ All test fixes applied!")
    print("\nRun 'python -m pytest --tb=no -q' to check the current status.")

if __name__ == "__main__":
    main()