"""
Utility functions for the OpenAPI client generator.
"""

import re
import keyword
from typing import Dict, Any, Union, Optional


def sanitize_python_identifier(name: str) -> str:
    """Sanitize identifier to avoid Python keywords and invalid names."""
    # If it's a Python keyword, append underscore
    if keyword.iskeyword(name):
        return f"{name}_"

    # If it starts with a digit, prepend underscore
    if name and name[0].isdigit():
        return f"_{name}"

    return name


def sanitize_model_name(model_name: str) -> str:
    """Sanitize model name to be a valid Python identifier."""
    # Replace dots, spaces, and other invalid characters with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", model_name)
    # Ensure it doesn't start with a digit
    if sanitized[0].isdigit():
        sanitized = f"Model_{sanitized}"
    # Remove multiple consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove trailing underscores
    sanitized = sanitized.strip("_")
    return sanitized


def to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    # Sanitize invalid characters
    sanitized = re.sub(r"[^a-zA-Z0-9_{}]", "_", name)

    # Convert version placeholders {id} to _id_
    sanitized = re.sub(r"\{([^}]+)\}", r"_\1_", sanitized)

    # Clean up patterns
    sanitized = re.sub(r"_api_v\d*_", "_", sanitized)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")

    # Handle camelCase and PascalCase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", sanitized)
    result = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    # Final cleanup
    result = re.sub(r"_+", "_", result).strip("_")

    # Ensure valid identifier
    if result and result[0].isdigit():
        result = f"op_{result}"

    if not result:
        result = "operation"

    return result


def to_pascal_case(name: str) -> str:
    """Convert string to PascalCase."""
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def get_python_type(
    type_def: Union[str, Dict[str, Any]], format_str: Optional[str] = None, quote_refs: bool = True
) -> str:
    """Convert OpenAPI/Swagger type to Python type.

    Accepts either a simple type string (e.g. "string") or a dict coming from
    an OpenAPI schema. Returns a textual Python type hint like "str", "int",
    or "List[Foo]".

    Args:
        type_def: The type definition (string or dict)
        format_str: Optional format string
        quote_refs: If True, quote $ref types (for TYPE_CHECKING imports), else for annotations
    """
    # Normalize to a dict-like structure for lookups
    if isinstance(type_def, str):
        type_str: Optional[str] = type_def
        type_def_dict: Dict[str, Any] = {"type": type_str, "format": format_str}
    else:
        type_def_dict = type_def

    # Determine nullability early
    nullable = bool(type_def_dict.get("nullable", False))

    # Handle $ref to another schema - check this FIRST before extracting type
    if isinstance(type_def, dict) and "$ref" in type_def_dict:
        ref = type_def_dict["$ref"]
        # Extract model name from ref like "#/components/schemas/ModelName"
        model_name = ref.split("/")[-1]
        # Split into namespace parts and get only the class name (last part)
        parts = model_name.split(".")
        class_name = sanitize_model_name(parts[-1]) if parts else sanitize_model_name(model_name)
        # Return as quoted string for forward reference if requested
        result_type = f"'{class_name}'" if quote_refs else class_name
        return f"Optional[{result_type}]" if nullable else result_type

    type_str = type_def_dict.get("type")

    type_mapping: Dict[str, str] = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "List",
        "object": "Dict[str, Any]",
        "file": "Any",
    }

    if type_str == "array":
        items = type_def_dict.get("items", {})
        # Pass through quote_refs for inner type as well
        item_type = get_python_type(items, quote_refs=quote_refs) if isinstance(items, dict) else get_python_type(items)
        result = f"List[{item_type}]"
        return f"Optional[{result}]" if nullable else result

    if type_str in type_mapping:
        result = type_mapping[type_str]
        return f"Optional[{result}]" if nullable else result

    if type_str is None:
        result = "str"
        return f"Optional[{result}]" if nullable else result

    result = "Any"
    return f"Optional[{result}]" if nullable else result
