import pytest
from fastapi.routing import APIRoute
from pydantic import TypeAdapter

from application import app
from constants.api_examples import OPERATION_EXAMPLES


def api_routes(routes):
    """APIRoutes of the app, including those inside included routers (wrapped since FastAPI 0.142)."""
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
        elif hasattr(route, "original_router"):
            yield from api_routes(route.original_router.routes)


ROUTES = {
    f"{method} {route.path}": route
    for route in api_routes(app.routes)
    if route.include_in_schema
    for method in route.methods
}


def test_every_operation_has_examples():
    assert set(ROUTES) == set(OPERATION_EXAMPLES)


def assert_round_trips(model, example, partial=False):
    """The example validates and serializes back unchanged, so it has no extra or misspelled fields.

    A response example must list every field; a request example (partial) may leave out optional ones.
    """
    adapter = TypeAdapter(model)
    value = adapter.validate_python(example, by_name=True)
    assert adapter.dump_python(value, mode="json", exclude_unset=partial) == example


@pytest.mark.parametrize("operation", sorted(ROUTES))
def test_examples_match_the_route_models(operation):
    route = ROUTES[operation]
    examples = OPERATION_EXAMPLES[operation]

    if route.body_field is not None:
        assert "request" in examples, f"{operation} takes a body but has no request example"
        assert_round_trips(route.body_field.field_info.annotation, examples["request"], partial=True)
    if route.response_model is not None:
        assert "response" in examples, f"{operation} has no response example"
        assert_round_trips(route.response_model, examples["response"])


def test_openapi_carries_the_examples():
    schema = app.openapi()
    operation = schema["paths"]["/channels/{channel_id}/videos/fetch"]["post"]

    assert operation["parameters"][0]["example"] == "UCslugpmYWJiZK5rbvtcaV7Q"
    assert operation["requestBody"]["content"]["application/json"]["example"]["max_videos"] == 50
    assert operation["responses"]["200"]["content"]["application/json"]["example"]["videos_saved"] == 1
    assert operation["responses"]["404"]["content"]["application/json"]["example"] == {
        "detail": "Channel not found"
    }
    comments = schema["paths"]["/videos/{video_id}/comments"]["get"]["responses"]["404"]
    assert comments["content"]["application/json"]["example"] == {"detail": "Video not found"}
