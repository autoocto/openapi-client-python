"""
Model generator for OpenAPI/Swagger specifications.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .utils import sanitize_model_name, sanitize_python_identifier, to_snake_case, get_python_type


class ModelGenerator:
    """Generates strongly-typed model classes from schema definitions."""

    def __init__(self, schemas: Dict[str, Any], output_dir: Path) -> None:
        """Initialize the model generator."""
        self.schemas = schemas
        self.output_dir = output_dir
        self.models_dir = output_dir / "models"
        self.base_dir = output_dir / "base"

    def generate_models(self) -> None:
        """Generate all model classes."""
        # Create required directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Generate base model
        self._generate_base_model()

        # Generate each model
        for model_name, model_def in self.schemas.items():
            self._generate_model_class(model_name, model_def)

        # Generate models __init__.py
        self._generate_models_init()

    def _generate_base_model(self) -> None:
        """Generate the base model class that all models inherit from."""
        base_model_content = '''"""
Base model class for all generated models.
"""

import json
from typing import Dict, Any, TypeVar, Type


T = TypeVar('T', bound='BaseModel')


class BaseModel:
    """Base class for all generated model classes with common serialization methods."""

    def __init__(self, data: Dict[str, Any] | None = None):
        """Initialize the model with optional data dictionary."""
        self._data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with nested object support."""
        result = {}
        for key, value in self._data.items():
            if hasattr(value, 'to_dict'):
                # Handle nested model objects
                result[key] = value.to_dict()
            elif isinstance(value, list):
                # Handle lists that might contain model objects
                result[key] = [
                    item.to_dict() if hasattr(item, "to_dict") else item for item in value
                ]
            else:
                result[key] = value
        return result

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create model from dictionary."""
        return cls(data)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create model from JSON string."""
        return cls(json.loads(json_str))
'''
        # Write base model
        base_model_path = self.base_dir / "base_model.py"
        with open(base_model_path, "w", encoding="utf-8") as f:
            f.write(base_model_content)

        # Create __init__.py for base package
        init_path = self.base_dir / "__init__.py"
        with open(init_path, "w", encoding="utf-8") as f:
            init_content = (
                '"""Base package for generated models."""\n\n'
                "from .base_model import BaseModel\n\n"
                '__all__ = ["BaseModel"]\n'
            )
            f.write(init_content)

    def _generate_model_class(self, model_name: str, model_def: Dict[str, Any]) -> None:
        """Generate a single strongly-typed model class."""
        parts = model_name.split(".")

        if len(parts) >= 2:
            # Last part is class name, second-to-last is folder
            class_name = sanitize_model_name(parts[-1])
            folder_name = sanitize_model_name(parts[-2])

            # Everything before the last two parts is the hierarchy
            hierarchy_parts = parts[:-2] if len(parts) > 2 else []

            # Build directory path: models/ + hierarchy + folder
            model_dir = self.models_dir
            for part in hierarchy_parts:
                model_dir = model_dir / sanitize_model_name(part)
            model_dir = model_dir / folder_name

            model_dir.mkdir(parents=True, exist_ok=True)
            file_path = model_dir / f"{class_name}.py"

            # Current namespace for imports includes hierarchy + folder
            current_namespace = [sanitize_model_name(p) for p in hierarchy_parts] + [folder_name]
        else:
            # Single part - just use as class name in models root
            class_name = sanitize_model_name(model_name)
            file_path = self.models_dir / f"{class_name}.py"
            current_namespace = []

        # Extract properties
        properties = model_def.get("properties", {})
        required = model_def.get("required", [])

        # Check if this is an enum
        enum_values = model_def.get("enum")

        content = self._generate_model_content(
            class_name, model_name, properties, required, current_namespace, enum_values
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_model_content(
        self,
        class_name: str,
        original_name: str,
        properties: Dict[str, Any],
        required: List[str],
        current_namespace: List[str],
        enum_values: Optional[List[str]] = None,
    ) -> str:
        """Generate the content for a model class."""
        # Check if this is an enum
        if enum_values:
            return self._generate_enum_content(
                class_name, original_name, enum_values, current_namespace
            )

        # Collect referenced models for TYPE_CHECKING imports
        referenced_models = self._collect_referenced_models(properties, current_namespace)

        imports = """from __future__ import annotations

from typing import List, Union, Optional, Dict, Any"""

        # Add TYPE_CHECKING imports for referenced models
        if referenced_models:
            imports += ", TYPE_CHECKING\n\nif TYPE_CHECKING:"
            for ref_import, ref_class in sorted(referenced_models):
                imports += f"\n    from {ref_import} import {ref_class}"

        base_import_path = "." * (
            len(current_namespace) + 2
        )  # +2 for models folder and current file
        imports += f"\n\nfrom {base_import_path}base.base_model import BaseModel"

        class_definition = f"""


class {class_name}(BaseModel):
    \"\"\"
    Strongly-typed model class for {original_name}
    
    Generated from OpenAPI/Swagger specification
    \"\"\"

{self._generate_model_properties(properties, required)}"""

        return imports + class_definition

    def _generate_enum_content(
        self,
        class_name: str,
        original_name: str,
        enum_values: List[str],
        current_namespace: List[str],
    ) -> str:
        """Generate the content for an enum class."""
        imports = """from __future__ import annotations

from typing import List, Union, Optional, Dict, Any"""

        # Calculate relative import path based on namespace depth
        base_import_path = "." * (
            len(current_namespace) + 2
        )  # +2 for models folder and current file
        imports += f"\n\nfrom {base_import_path}base.base_model import BaseModel" ""

        # Generate enum constants
        enum_constants = []
        for value in enum_values:
            # Convert enum value to valid Python identifier
            const_name = sanitize_python_identifier(
                value.upper().replace("-", "_").replace(" ", "_")
            )
            enum_constants.append(f'    {const_name} = "{value}"')

        constants_str = "\n".join(enum_constants)

        class_definition = f"""


class {class_name}(BaseModel):
    \"\"\"
    Enum class for {original_name}
    
    Generated from OpenAPI/Swagger specification
    
    Possible values:
{chr(10).join(f"    - {value}" for value in enum_values)}
    \"\"\"

    # Enum constants
{constants_str}
"""

        return imports + class_definition

    def _collect_referenced_models(
        self, properties: Dict[str, Any], current_namespace: List[str]
    ) -> List[tuple]:
        """Collect all referenced model names from properties with their import paths."""
        referenced = set()

        for prop_def in properties.values():
            # Check for direct $ref
            if "$ref" in prop_def:
                ref = prop_def["$ref"]
                model_name = ref.split("/")[-1]
                import_path, class_name = self._get_model_import_path(model_name, current_namespace)
                referenced.add((import_path, class_name))

            # Check for array items with $ref
            if prop_def.get("type") == "array":
                items = prop_def.get("items", {})
                if "$ref" in items:
                    ref = items["$ref"]
                    model_name = ref.split("/")[-1]
                    import_path, class_name = self._get_model_import_path(
                        model_name, current_namespace
                    )
                    referenced.add((import_path, class_name))

        return list(referenced)

    def _get_model_import_path(self, model_name: str, current_namespace: List[str]) -> tuple:
        """Get the import path and class name for a model.

        Calculate relative import based on the current namespace and target namespace.
        With new structure: hierarchy.folder.ClassName
        """
        parts = model_name.split(".")

        if len(parts) >= 2:
            # Target: last part is class, second-to-last is folder, rest is hierarchy
            class_name = sanitize_model_name(parts[-1])
            folder_name = sanitize_model_name(parts[-2])
            hierarchy_parts = [sanitize_model_name(p) for p in parts[:-2]] if len(parts) > 2 else []

            # Target namespace includes hierarchy + folder
            target_namespace = hierarchy_parts + [folder_name]
        else:
            # Target has no namespace (root level)
            target_namespace = []
            class_name = sanitize_model_name(model_name)

        # Find common prefix
        common_len = 0
        for i in range(min(len(current_namespace), len(target_namespace))):
            if current_namespace[i] == target_namespace[i]:
                common_len += 1
            else:
                break

        # Calculate how many levels to go up
        up_levels = len(current_namespace) - common_len

        # Calculate path from common ancestor to target
        down_path = target_namespace[common_len:]

        # Build import path
        if up_levels == 0 and len(down_path) == 0:
            # Same directory
            import_path = f".{class_name}"
        else:
            # Need to navigate
            dots = "." * (up_levels + 1)
            if down_path:
                import_path = f"{dots}{'.'.join(down_path)}.{class_name}"
            else:
                import_path = f"{dots}{class_name}"

        return import_path, class_name

    def _generate_model_properties(self, properties: Dict[str, Any], required: List[str]) -> str:
        """Generate property getters and setters for a model."""
        prop_code = []

        for prop_name, prop_def in properties.items():
            prop_type = get_python_type(prop_def)

            # Sanitize property name to avoid Python keywords
            python_prop_name = sanitize_python_identifier(to_snake_case(prop_name))

            # Property getter
            prop_code.append(
                f"""    @property
    def {python_prop_name}(self) -> {prop_type}:
        \"\"\"Get {prop_name}\"\"\"
        return self._data.get("{prop_name}")"""
            )

            # Property setter
            prop_code.append(
                f"""    @{python_prop_name}.setter
    def {python_prop_name}(self, value: {prop_type}):
        \"\"\"Set {prop_name}\"\"\"
        self._data["{prop_name}"] = value"""
            )

            prop_code.append("")

        return "\n".join(prop_code)

    def _generate_models_init(self) -> None:
        """Generate __init__.py files for models package and all subdirectories."""
        # Track all directories and their models
        dir_models: Dict[Path, List[Tuple[str, str]]] = (
            {}
        )  # Maps directory path to list of (import_path, class_name) tuples

        for model_name in self.schemas.keys():
            parts = model_name.split(".")

            if len(parts) >= 2:
                # New structure: last is class, second-to-last is folder, rest is hierarchy
                class_name = sanitize_model_name(parts[-1])
                folder_name = sanitize_model_name(parts[-2])
                hierarchy_parts = (
                    [sanitize_model_name(p) for p in parts[:-2]] if len(parts) > 2 else []
                )

                # Build path to the folder containing the model
                model_dir = self.models_dir
                for part in hierarchy_parts:
                    model_dir = model_dir / part
                model_dir = model_dir / folder_name

                # Track this directory and model
                if model_dir not in dir_models:
                    dir_models[model_dir] = []
                dir_models[model_dir].append((f".{class_name}", class_name))

                # Track all parent directories for __init__ files
                current_path = self.models_dir
                for part in hierarchy_parts:
                    current_path = current_path / part
                    if current_path not in dir_models:
                        dir_models[current_path] = []
            else:
                # Single part - add to root models directory
                class_name = sanitize_model_name(model_name)
                if self.models_dir not in dir_models:
                    dir_models[self.models_dir] = []
                dir_models[self.models_dir].append((f".{class_name}", class_name))

        # Ensure models directory has __init__.py even if empty
        if self.models_dir not in dir_models:
            dir_models[self.models_dir] = []

        # Generate __init__.py for each directory
        for dir_path, models in dir_models.items():
            init_content = "# Generated strongly-typed model classes\n\n"

            # Add imports
            for import_path, class_name in sorted(models):
                init_content += f"from {import_path} import {class_name}\n"

            # Add subdirectory imports if this is not a leaf directory
            if dir_path.exists():
                subdirs = [
                    d.name for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith("__")
                ]
                for subdir in sorted(subdirs):
                    init_content += f"from . import {subdir}\n"
            else:
                subdirs = []

            # Add __all__ list
            all_names = [class_name for _, class_name in sorted(models)]
            all_names.extend(sorted(subdirs))
            init_content += f"\n__all__ = {all_names}\n"

            init_file = dir_path / "__init__.py"
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(init_content)
