from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError
from youtube_transcript_api._errors import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
)

from application import app
from services import transcript_service
from services.transcript_service import (
    choose_transcript,
    is_block_error,
    is_temporary_error,
    redact_sensitive,
)

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-client-key"}


@dataclass
class DummyTranscript:
    language_code: str
    language: str
    is_generated: bool


def test_choose_transcript_priorities():
    # 1. Manual en over manual ur
    t_en_man = DummyTranscript("en", "English", False)
    t_ur_man = DummyTranscript("ur", "Urdu", False)
    assert choose_transcript([t_ur_man, t_en_man], ["en", "ur", "hi"]) == t_en_man

    # 2. Manual ur over auto en (manual of lower preferred over auto of higher preferred)
    t_en_gen = DummyTranscript("en", "English", True)
    assert choose_transcript([t_en_gen, t_ur_man], ["en", "ur", "hi"]) == t_ur_man

    # 3. Auto en over auto ur
    t_ur_gen = DummyTranscript("ur", "Urdu", True)
    assert choose_transcript([t_ur_gen, t_en_gen], ["en", "ur", "hi"]) == t_en_gen

    # 4. Regional code prefix match: en-US matches en
    t_en_us = DummyTranscript("en-US", "English (United States)", True)
    assert choose_transcript([t_en_us], ["en", "ur", "hi"]) == t_en_us

    # 5. Original video default language when none of preferred exist
    t_es_man = DummyTranscript("es", "Spanish", False)
    t_fr_man = DummyTranscript("fr", "French", False)
    assert (
        choose_transcript(
            [t_fr_man, t_es_man],
            preferred_languages=["en", "ur", "hi"],
            video_default_language="es",
        )
        == t_es_man
    )

    # 6. Fallback to any manual transcript
    assert choose_transcript([t_fr_man], ["en", "ur", "hi"]) == t_fr_man

    # 7. Fallback to any auto transcript
    t_de_gen = DummyTranscript("de", "German", True)
    assert choose_transcript([t_de_gen], ["en", "ur", "hi"]) == t_de_gen

    # 8. Empty returns None
    assert choose_transcript([], ["en"]) is None


def test_redact_sensitive(monkeypatch):
    from pydantic import SecretStr

    dummy_settings = MagicMock()
    dummy_settings.transcript_proxy_url = SecretStr("http://user:secret123@proxy.io:8080")
    dummy_settings.youtube_api_key = SecretStr("AIzaSySecretApiKey456")
    monkeypatch.setattr(transcript_service, "get_settings", lambda: dummy_settings)

    text = "Error connecting to http://user:secret123@proxy.io:8080 with key AIzaSySecretApiKey456 failed"
    redacted = redact_sensitive(text)
    assert "secret123" not in redacted
    assert "AIzaSySecretApiKey456" not in redacted
    assert "[REDACTED_PROXY]" in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_is_block_error():
    assert is_block_error(RequestBlocked("vid123"))
    assert is_block_error(IpBlocked("vid123"))

    resp_429 = Response()
    resp_429.status_code = 429
    assert is_block_error(HTTPError(response=resp_429))

    resp_403 = Response()
    resp_403.status_code = 403
    assert is_block_error(HTTPError(response=resp_403))

    assert is_block_error(Exception("Too Many Requests: ip blocked"))
    assert not is_block_error(Exception("Normal syntax error"))


def test_is_temporary_error():
    assert is_temporary_error(RequestsConnectionError("timed out"))

    resp_503 = Response()
    resp_503.status_code = 503
    assert is_temporary_error(HTTPError(response=resp_503))

    assert not is_temporary_error(TranscriptsDisabled("vid123"))
    assert not is_temporary_error(NoTranscriptFound("vid123", ["en"], MagicMock()))
    assert not is_temporary_error(RequestBlocked("vid123"))


def test_get_transcript_requires_auth():
    resp = client.get("/videos/test_vid/transcript")
    assert resp.status_code == 401


def test_get_transcript_not_found(monkeypatch):
    async def mock_get(video_id, format_type):
        raise transcript_service.VideoNotFoundError(video_id)

    monkeypatch.setattr(transcript_service, "get_stored_transcript", mock_get)
    resp = client.get("/videos/missing_vid/transcript", headers=AUTH_HEADERS)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Video not found"


def test_get_transcript_success(monkeypatch):
    async def mock_get(video_id, format_type):
        return {
            "id": 1,
            "video_id": video_id,
            "status": "available",
            "language_code": "en",
            "language_name": "English",
            "is_generated": False,
            "full_text": "Sample text",
            "segment_count": 1,
            "attempt_count": 1,
            "last_error": None,
            "fetched_at": datetime.now(UTC),
            "segments": [
                {
                    "position": 0,
                    "start_seconds": 0.0,
                    "duration_seconds": 2.5,
                    "text": "Sample text",
                }
            ],
        }

    monkeypatch.setattr(transcript_service, "get_stored_transcript", mock_get)
    resp = client.get("/videos/vid123/transcript", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == "vid123"
    assert body["status"] == "available"
    assert body["full_text"] == "Sample text"
    assert len(body["segments"]) == 1


def test_fetch_video_transcript_blocked_returns_503(monkeypatch):
    async def mock_fetch(video_id, preferred_languages=None):
        raise transcript_service.TranscriptBlockedError("IP Blocked by YouTube")

    monkeypatch.setattr(transcript_service, "fetch_and_store_video_transcript", mock_fetch)
    resp = client.post(
        "/videos/vid123/transcript",
        headers=AUTH_HEADERS,
        json={"preferred_languages": ["en"]},
    )
    assert resp.status_code == 503
    assert "blocked" in resp.json()["detail"].lower()


def test_fetch_channel_transcripts_endpoint(monkeypatch):
    async def mock_channel_transcripts(channel_id, preferred_languages=None, only_missing=True):
        return {
            "channel_id": channel_id,
            "total_videos": 10,
            "processed": 10,
            "available": 8,
            "none": 1,
            "disabled": 1,
            "failed": 0,
            "blocked": 0,
            "step_status": "done",
        }

    monkeypatch.setattr(transcript_service, "fetch_and_store_channel_transcripts", mock_channel_transcripts)
    resp = client.post("/channels/chan123/transcripts", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel_id"] == "chan123"
    assert data["available"] == 8
    assert data["step_status"] == "done"


def test_list_channel_transcripts_status_endpoint(monkeypatch):
    async def mock_status_list(channel_id, status_filter=None, skip=0, take=50):
        return [
            {
                "video_id": "v1",
                "title": "Video 1",
                "transcript_status": "available",
                "language_code": "en",
                "is_generated": False,
                "attempt_count": 1,
                "last_error": None,
                "fetched_at": None,
            }
        ], 1

    monkeypatch.setattr(transcript_service, "list_channel_videos_transcript_status", mock_status_list)
    resp = client.get("/channels/chan123/transcripts/status", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["video_id"] == "v1"
    assert data["items"][0]["transcript_status"] == "available"
