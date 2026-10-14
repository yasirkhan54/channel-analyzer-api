from fastapi.testclient import TestClient

from application import app
from services import channel_management_service
from services.channel_management_service import ChannelBusyError
from tests.test_channel_read import make_channel

client = TestClient(app)
HEADERS = {"X-API-Key": "test-client-key"}


def stub(monkeypatch, module, name, value):
    async def fake(*_args, **_kwargs):
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(module, name, fake)


def test_delete_channel(monkeypatch):
    stub(monkeypatch, channel_management_service, "delete_channel", True)

    response = client.delete("/channels/UC1", headers=HEADERS)

    assert response.status_code == 204
    assert response.content == b""


def test_delete_unknown_channel(monkeypatch):
    stub(monkeypatch, channel_management_service, "delete_channel", False)

    assert client.delete("/channels/UC1", headers=HEADERS).status_code == 404


def test_delete_refused_while_job_active(monkeypatch):
    stub(monkeypatch, channel_management_service, "delete_channel", ChannelBusyError())

    assert client.delete("/channels/UC1", headers=HEADERS).status_code == 409


def test_mark_channel_tracked(monkeypatch):
    stub(monkeypatch, channel_management_service, "set_tracked", make_channel(tracked=True))

    response = client.patch("/channels/UC1", json={"tracked": True}, headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["tracked"] is True


def test_tracking_requires_boolean():
    assert client.patch("/channels/UC1", json={"tracked": "maybe"}, headers=HEADERS).status_code == 422
