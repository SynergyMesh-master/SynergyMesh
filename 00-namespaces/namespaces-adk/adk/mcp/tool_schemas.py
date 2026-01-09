"""
Tool Schemas: Defines schemas for tool inputs, outputs, and metadata.

This module provides schema validation, management, and conversion
for MCP tool schemas.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import copy

from ..observability.logging import Logger


class SchemaFormat(Enum):
    """Schema format types."""
    JSON_SCHEMA = "json_schema"
    OPENAPI = "openapi"
    MCP_NATIVE = "mcp_native"
    PROTOBUF = "protobuf"


@dataclass
class ParameterSchema:
    """Schema for a tool parameter."""
    name: str
    type: str
    description: str = ""
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    properties: Optional[Dict[str, "ParameterSchema"]] = None
    items: Optional["ParameterSchema"] = None  # For array types
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = {
            "type": self.type,
            "description": self.description
        }
        
        if self.default is not None:
            schema["default"] = self.default
        
        if self.enum:
            schema["enum"] = self.enum
        
        if self.min is not None:
            if self.type == "string":
                schema["minLength"] = self.min
            else:
                schema["minimum"] = self.min
        
        if self.max is not None:
            if self.type == "string":
                schema["maxLength"] = self.max
            else:
                schema["maximum"] = self.max
        
        if self.pattern:
            schema["pattern"] = self.pattern
        
        if self.properties:
            schema["properties"] = {
                k: v.to_json_schema()
                for k, v in self.properties.items()
            }
            schema["required"] = [
                k for k, v in self.properties.items()
                if v.required
            ]
        
        if self.items:
            schema["items"] = self.items.to_json_schema()
        
        return schema


@dataclass
class ToolSchema:
    """Complete schema for a tool."""
    name: str
    description: str
    input_schema: ParameterSchema
    output_schema: Optional[ParameterSchema] = None
    format: SchemaFormat = SchemaFormat.JSON_SCHEMA
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema.to_json_schema(),
            "output_schema": self.output_schema.to_json_schema() if self.output_schema else None,
            "format": self.format.value,
            "version": self.version,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class SchemaValidator:
    """Validates tool schemas and inputs."""
    
    def __init__(self):
        self.logger = Logger(name="schema.validator")
    
    def validate_schema(self, schema: ToolSchema) -> bool:
        """
        Validate a tool schema.
        
        Args:
            schema: Tool schema to validate
            
        Returns:
            True if valid
        """
        # Check required fields
        if not schema.name:
            self.logger.error("Schema missing name")
            return False
        
        if not schema.description:
            self.logger.error(f"Schema missing description: {schema.name}")
            return False
        
        if not schema.input_schema:
            self.logger.error(f"Schema missing input_schema: {schema.name}")
            return False
        
        return True
    
    def validate_input(
        self,
        schema: ParameterSchema,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate input data against a schema.
        
        Args:
            schema: Parameter schema
            data: Input data to validate
            
        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        if schema.required and schema.name not in data:
            return False, f"Required field missing: {schema.name}"
        
        # Skip validation if field not present and not required
        if schema.name not in data:
            return True, None
        
        value = data[schema.name]
        
        # Type validation
        if not self._validate_type(schema.type, value):
            return False, f"Type mismatch for {schema.name}: expected {schema.type}"
        
        # Enum validation
        if schema.enum and value not in schema.enum:
            return False, f"Invalid value for {schema.name}: must be one of {schema.enum}"
        
        # Min/Max validation
        if schema.min is not None:
            if isinstance(value, (int, float)) and value < schema.min:
                return False, f"Value for {schema.name} below minimum: {schema.min}"
            elif isinstance(value, str) and len(value) < schema.min:
                return False, f"Length of {schema.name} below minimum: {schema.min}"
        
        if schema.max is not None:
            if isinstance(value, (int, float)) and value > schema.max:
                return False, f"Value for {schema.name} above maximum: {schema.max}"
            elif isinstance(value, str) and len(value) > schema.max:
                return False, f"Length of {schema.name} above maximum: {schema.max}"
        
        # Pattern validation
        if schema.pattern and isinstance(value, str):
            import re
            if not re.match(schema.pattern, value):
                return False, f"Value for {schema.name} does not match pattern"
        
        # Nested object validation
        if schema.properties and isinstance(value, dict):
            for prop_schema in schema.properties.values():
                is_valid, error = self.validate_input(prop_schema, value)
                if not is_valid:
                    return False, error
        
        # Array item validation
        if schema.items and isinstance(value, list):
            for i, item in enumerate(value):
                # Create a temporary schema for the item
                item_schema = copy.deepcopy(schema.items)
                item_schema.name = f"{schema.name}[{i}]"
                
                is_valid, error = self.validate_input(
                    item_schema,
                    {item_schema.name: item}
                )
                if not is_valid:
                    return False, error
        
        return True, None
    
    def _validate_type(self, expected_type: str, value: Any) -> bool:
        """Validate value type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if not expected_python_type:
            return True  # Unknown type, allow
        
        if isinstance(value, expected_python_type):
            return True
        
        # Special case for number/integer with string values
        if expected_type in ["number", "integer"] and isinstance(value, str):
            try:
                if expected_type == "integer":
                    int(value)
                else:
                    float(value)
                return True
            except ValueError:
                return False
        
        return False


class SchemaConverter:
    """Converts between different schema formats."""
    
    @staticmethod
    def json_schema_to_openapi(json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON Schema to OpenAPI format."""
        # OpenAPI 3.0 uses a slightly different structure
        # For now, return as-is with minor adjustments
        openapi_schema = copy.deepcopy(json_schema)
        
        # Convert type "null" to nullable property
        if json_schema.get("type") == "null":
            openapi_schema["nullable"] = True
            openapi_schema.pop("type", None)
        
        return openapi_schema
    
    @staticmethod
    def openapi_to_json_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI format to JSON Schema."""
        json_schema = copy.deepcopy(openapi_schema)
        
        # Convert nullable to "null" type
        if openapi_schema.get("nullable"):
            if "type" in json_schema:
                if isinstance(json_schema["type"], str):
                    json_schema["type"] = [json_schema["type"], "null"]
                elif isinstance(json_schema["type"], list):
                    json_schema["type"].append("null")
            json_schema.pop("nullable", None)
        
        return json_schema
    
    @staticmethod
    def mcp_native_to_json_schema(mcp_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP native format to JSON Schema."""
        json_schema = {
            "type": mcp_schema.get("type", "object"),
            "description": mcp_schema.get("description", "")
        }
        
        if "properties" in mcp_schema:
            json_schema["properties"] = mcp_schema["properties"]
        
        if "required" in mcp_schema:
            json_schema["required"] = mcp_schema["required"]
        
        if "default" in mcp_schema:
            json_schema["default"] = mcp_schema["default"]
        
        return json_schema


class ToolSchemas:
    """
    Manager for tool schemas.
    
    Features:
    - Schema storage and retrieval
    - Schema validation
    - Format conversion
    - Version management
    - Schema evolution
    """
    
    def __init__(self):
        self.logger = Logger(name="tool.schemas")
        
        # Schema registry
        self._schemas: Dict[str, Dict[str, ToolSchema]] = {}  # tool_name -> version -> schema
        
        # Validators and converters
        self.validator = SchemaValidator()
        self.converter = SchemaConverter()
    
    def register_schema(self, schema: ToolSchema) -> bool:
        """
        Register a tool schema.
        
        Args:
            schema: Tool schema to register
            
        Returns:
            True if registered successfully
        """
        # Validate schema
        if not self.validator.validate_schema(schema):
            return False
        
        # Store schema
        if schema.name not in self._schemas:
            self._schemas[schema.name] = {}
        
        self._schemas[schema.name][schema.version] = schema
        
        self.logger.info(f"Registered schema: {schema.name}@{schema.version}")
        return True
    
    def get_schema(
        self,
        tool_name: str,
        version: Optional[str] = None
    ) -> Optional[ToolSchema]:
        """
        Get a tool schema.
        
        Args:
            tool_name: Name of the tool
            version: Schema version (if None, gets latest)
            
        Returns:
            Tool schema or None
        """
        schemas = self._schemas.get(tool_name, {})
        
        if not schemas:
            return None
        
        if version:
            return schemas.get(version)
        
        # Get latest version
        return sorted(schemas.values(), key=lambda s: s.version)[-1]
    
    def list_schemas(self) -> List[ToolSchema]:
        """List all registered schemas."""
        schemas = []
        for version_map in self._schemas.values():
            schemas.extend(version_map.values())
        return schemas
    
    def delete_schema(
        self,
        tool_name: str,
        version: str
    ) -> bool:
        """
        Delete a tool schema.
        
        Args:
            tool_name: Name of the tool
            version: Schema version
            
        Returns:
            True if deleted
        """
        if tool_name in self._schemas and version in self._schemas[tool_name]:
            del self._schemas[tool_name][version]
            return True
        return False
    
    def convert_schema(
        self,
        schema: ToolSchema,
        target_format: SchemaFormat
    ) -> Dict[str, Any]:
        """
        Convert schema to a different format.
        
        Args:
            schema: Tool schema
            target_format: Target format
            
        Returns:
            Converted schema
        """
        if target_format == SchemaFormat.JSON_SCHEMA:
            return schema.to_dict()
        elif target_format == SchemaFormat.OPENAPI:
            json_schema = schema.to_dict()
            return self.converter.json_schema_to_openapi(json_schema)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
    
    def validate_tool_input(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        version: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate tool input against schema.
        
        Args:
            tool_name: Name of the tool
            input_data: Input data to validate
            version: Schema version
            
        Returns:
            (is_valid, error_message)
        """
        schema = self.get_schema(tool_name, version)
        if not schema:
            return False, f"Schema not found for tool: {tool_name}"
        
        return self.validator.validate_input(schema.input_schema, input_data)