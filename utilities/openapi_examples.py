from typing import Any

from constants.api_examples import ERROR_EXAMPLES, OPERATION_EXAMPLES, PATH_PARAMETER_EXAMPLES

ERROR_SCHEMA_REF = "#/components/schemas/ErrorResponse"
PATH_THINGS = (
    ("{job_id}", "Fetch job"),
    ("{search_id}", "Search"),
    ("{playlist_id}", "Playlist"),
    ("{video_id}", "Video"),
    ("{channel_id}", "Channel"),
)


def _thing(path: str) -> str:
    """The resource a 404 is about: the last ID in the path wins (/videos/{video_id} -> Video)."""
    positions = [(path.rfind(marker), name) for marker, name in PATH_THINGS if marker in path]
    return max(positions)[1] if positions else "Resource"


def _json_content(container: dict[str, Any]) -> dict[str, Any] | None:
    return container.get("content", {}).get("application/json")


def add_examples(schema: dict[str, Any]) -> dict[str, Any]:
    """Put request, response, error and path parameter examples into an OpenAPI schema, in place."""
    for path, operations in schema.get("paths", {}).items():
        for method, operation in operations.items():
            examples = OPERATION_EXAMPLES.get(f"{method.upper()} {path}", {})

            for parameter in operation.get("parameters", []):
                if parameter.get("in") == "path" and parameter["name"] in PATH_PARAMETER_EXAMPLES:
                    parameter["example"] = PATH_PARAMETER_EXAMPLES[parameter["name"]]

            body = _json_content(operation.get("requestBody", {}))
            if body is not None and "request" in examples:
                body["example"] = examples["request"]

            for status, response in operation.get("responses", {}).items():
                content = _json_content(response)
                if content is None:
                    continue
                if status in examples.get("errors", {}):
                    content["example"] = examples["errors"][status]
                elif status.startswith("2") and "response" in examples:
                    content["example"] = examples["response"]
                elif content.get("schema", {}).get("$ref") == ERROR_SCHEMA_REF and status in ERROR_EXAMPLES:
                    content["example"] = {"detail": ERROR_EXAMPLES[status].format(thing=_thing(path))}
    return schema
