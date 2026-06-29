"""OpenAPI schema post-processing for Swagger UI."""

from __future__ import annotations

from typing import Any

from app.models.openapi_examples import (
    DEFAULT_AUTH_ERROR,
    OPERATION_EXAMPLES,
    PROTECTED_PATH_PREFIXES,
)


def _first_example_value(content: dict[str, Any]) -> Any | None:
    """Extract the first example value from OpenAPI content."""
    if "example" in content:
        return content["example"]
    examples = content.get("examples") or {}
    for item in examples.values():
        if isinstance(item, dict) and "value" in item:
            return item["value"]
    return None


def _example_from_schema(schema: dict[str, Any] | None, components: dict[str, Any]) -> Any | None:
    """Build an example object from an OpenAPI schema or component reference."""
    if not schema:
        return None

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        schema = components.get("schemas", {}).get(ref_name, {})
        if not schema:
            return None

    if "example" in schema:
        return schema["example"]
    if "examples" in schema:
        examples = schema["examples"]
        if isinstance(examples, list) and examples:
            return examples[0]
        if isinstance(examples, dict) and examples:
            first = next(iter(examples.values()))
            return first.get("value", first) if isinstance(first, dict) else first

    if schema.get("type") == "array":
        item_example = _example_from_schema(schema.get("items", {}), components)
        return [item_example] if item_example is not None else []

    if schema.get("type") == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        if not properties:
            return {}
        built: dict[str, Any] = {}
        for key, prop in properties.items():
            if "example" in prop:
                built[key] = prop["example"]
            elif "default" in prop:
                built[key] = prop["default"]
            elif prop.get("type") == "object" or "properties" in prop:
                built[key] = _example_from_schema(prop, components)
            elif prop.get("type") == "array":
                built[key] = _example_from_schema(prop, components)
            elif prop.get("anyOf"):
                built[key] = _example_from_schema(prop["anyOf"][0], components)
            else:
                built[key] = None
        return built

    return None


def _resolve_example(
    content: dict[str, Any],
    components: dict[str, Any],
    override: Any | None = None,
) -> Any | None:
    """Pick the best available example for a request or response body."""
    if override is not None:
        return override

    existing = _first_example_value(content)
    if existing is not None:
        return existing

    schema = content.get("schema")
    return _example_from_schema(schema, components)


def _apply_example_only_content(example: Any) -> dict[str, Any]:
    """Expose only an example payload under application/json."""
    return {
        "application/json": {
            "example": example,
        }
    }


def _operation_key(method: str, path: str) -> tuple[str, str]:
    return method.lower(), path


def simplify_openapi_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Simplify Swagger bodies to example-only payloads for all operations.

    - Removes JSON Schema from request/response bodies
    - Injects curated examples for every documented endpoint
  """
    components = schema.get("components", {})
    paths = schema.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method, operation in path_item.items():
            if method.lower() not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
            }:
                continue
            if not isinstance(operation, dict):
                continue

            op_examples = OPERATION_EXAMPLES.get(_operation_key(method, path), {})
            request_override = op_examples.get("request")
            response_overrides: dict[str, Any] = op_examples.get("responses", {})

            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                content = request_body.get("content", {})
                json_content = content.get("application/json", {})
                example = _resolve_example(json_content, components, request_override)
                if example is not None:
                    request_body["content"] = _apply_example_only_content(example)

            responses = operation.get("responses", {})
            if not isinstance(responses, dict):
                continue

            for status_code, response in responses.items():
                if not isinstance(response, dict):
                    continue

                override = response_overrides.get(str(status_code))
                content = response.get("content", {})

                if not content and override is not None:
                    response["content"] = _apply_example_only_content(override)
                    response.pop("model", None)
                    continue

                json_content = content.get("application/json", {})
                if not json_content and override is None:
                    if str(status_code) == "401" and path.startswith(PROTECTED_PATH_PREFIXES):
                        response["content"] = _apply_example_only_content(DEFAULT_AUTH_ERROR)
                    continue

                example = _resolve_example(json_content, components, override)
                if example is None and str(status_code) == "401":
                    example = DEFAULT_AUTH_ERROR

                if example is not None:
                    response["content"] = _apply_example_only_content(example)
                    response.pop("model", None)

            if path.startswith(PROTECTED_PATH_PREFIXES) and "401" not in responses:
                responses["401"] = {
                    "description": "Missing or invalid access token.",
                    "content": _apply_example_only_content(DEFAULT_AUTH_ERROR),
                }

    schema["components"] = components
    if "schemas" in schema["components"]:
        schema["components"]["schemas"] = {}

    return schema


SWAGGER_UI_HIDE_MEDIA_TYPE_CSS = """
<style>
  .opblock-body select.content-type,
  .opblock-body .content-type-wrapper,
  .opblock-body .body-param-content-type,
  .opblock-body .response-content-type,
  .opblock-body .accept-header,
  .opblock-section .content-type,
  .response-controls .response-control-media-type,
  .response-controls .response-control-media-type__accept-message {
    display: none !important;
  }

  .model-box,
  .models,
  section.models {
    display: none !important;
  }
</style>
"""
