"""
Schema generator for capability parameter validation.

Generates Pydantic models from service method signatures via introspection,
eliminating the need for duplicate schema definitions.
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Type, get_type_hints, get_origin, get_args, Union

from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

# Parameters to exclude from generated schemas (injected by the system)
DEFAULT_EXCLUDE_PARAMS = {"self", "user_id", "db", "session", "redis", "request"}


def generate_input_schema_from_method(
    service_class: Type,
    method_name: str,
    exclude_params: set[str] | None = None,
    model_name_override: str | None = None,
) -> Type[BaseModel] | None:
    """
    Generate a Pydantic input schema by introspecting a service method.

    This enables automatic OpenAPI documentation and parameter validation
    without manually defining duplicate schemas.

    Args:
        service_class: The service class (e.g., ScreeningService)
        method_name: The method name (e.g., "get_maverick_stocks")
        exclude_params: Parameters to exclude (e.g., system-injected params)
        model_name_override: Custom name for the generated model

    Returns:
        Dynamically created Pydantic model, or None if no params

    Example:
        >>> from maverick_services import ScreeningService
        >>> InputModel = generate_input_schema_from_method(
        ...     ScreeningService,
        ...     "get_maverick_stocks",
        ...     exclude_params={"user_id"},
        ... )
        >>> # InputModel now has: limit: int = 20, filters: ScreeningFilter | None = None
    """
    exclude_params = (exclude_params or set()) | DEFAULT_EXCLUDE_PARAMS

    try:
        method = getattr(service_class, method_name)
    except AttributeError:
        logger.warning(
            f"Method {method_name} not found on {service_class.__name__}"
        )
        return None

    sig = inspect.signature(method)

    # Get type hints - handles forward references properly
    try:
        hints = get_type_hints(method)
    except Exception as e:
        logger.warning(
            f"Could not get type hints for {service_class.__name__}.{method_name}: {e}"
        )
        hints = {}

    fields: dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        if param_name in exclude_params:
            continue

        # Get type annotation (fall back to Any if not annotated)
        annotation = hints.get(param_name, Any)

        # Skip 'return' annotation if present
        if param_name == "return":
            continue

        # Get default value
        if param.default is inspect.Parameter.empty:
            # Required field - use ellipsis
            default = ...
        else:
            default = param.default

        # Handle Optional types - extract the inner type for better schema
        origin = get_origin(annotation)
        if origin is Union:
            args = get_args(annotation)
            # Check if it's Optional[X] (Union[X, None])
            if type(None) in args:
                # It's Optional - keep as is, Pydantic handles it
                pass

        fields[param_name] = (annotation, default)

    if not fields:
        logger.debug(
            f"No input parameters for {service_class.__name__}.{method_name}"
        )
        return None

    # Create model with proper name
    model_name = model_name_override or f"{service_class.__name__}_{method_name}_Input"

    try:
        model = create_model(model_name, **fields)
        logger.debug(
            f"Generated input schema {model_name} with fields: {list(fields.keys())}"
        )
        return model
    except Exception as e:
        logger.error(
            f"Failed to create model for {service_class.__name__}.{method_name}: {e}"
        )
        return None


def generate_schema_for_capability(capability: Any) -> Type[BaseModel] | None:
    """
    Generate input schema for a capability from its service method.

    If the capability already has an input_schema defined, returns that.
    Otherwise, introspects the service method to generate one.

    Args:
        capability: A Capability object

    Returns:
        Pydantic model for input validation, or None
    """
    # Use explicitly defined schema if available
    if hasattr(capability, "input_schema") and capability.input_schema is not None:
        return capability.input_schema

    # Generate from service method
    if not hasattr(capability, "service_class") or not hasattr(capability, "method_name"):
        return None

    return generate_input_schema_from_method(
        service_class=capability.service_class,
        method_name=capability.method_name,
        model_name_override=f"{capability.id}_Input",
    )


__all__ = [
    "generate_input_schema_from_method",
    "generate_schema_for_capability",
    "DEFAULT_EXCLUDE_PARAMS",
]
