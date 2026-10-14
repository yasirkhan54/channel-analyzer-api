import asyncio
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from prisma.enums import TranscriptStatus
from prisma.models import Transcript as PrismaTranscript
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeRequestFailed,
)
from youtube_transcript_api.proxies import GenericProxyConfig

from configurations.database_configuration import database
from configurations.environment_configuration import get_settings
from constants.application_constants import (
    DEFAULT_TRANSCRIPT_LANGUAGES,
    DEFAULT_TRANSCRIPT_MAX_ATTEMPTS,
    DEFAULT_TRANSCRIPT_PAUSE_SECONDS,
)

logger = logging.getLogger(__name__)


class VideoNotFoundError(Exception):
    def __init__(self, video_id: str):
        super().__init__(f"Video not found: {video_id}")
        self.video_id = video_id


class ChannelNotFoundError(Exception):
    def __init__(self, channel_id: str):
        super().__init__(f"Channel not found: {channel_id}")
        self.channel_id = channel_id


class TranscriptNotFoundError(Exception):
    def __init__(self, video_id: str):
        super().__init__(f"Transcript not found for video: {video_id}")
        self.video_id = video_id


class TranscriptBlockedError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class RawSegment:
    position: int
    start_seconds: float
    duration_seconds: float
    text: str


@dataclass
class ExtractedTranscript:
    video_id: str
    language_code: str
    language_name: str
    is_generated: bool
    full_text: str
    segments: list[RawSegment]


def redact_sensitive(text: str) -> str:
    """Removes sensitive proxy credentials and API keys from text."""
    settings = get_settings()
    if settings.transcript_proxy_url:
        proxy_val = settings.transcript_proxy_url.get_secret_value()
        if proxy_val and proxy_val in text:
            text = text.replace(proxy_val, "[REDACTED_PROXY]")
    if settings.youtube_api_key:
        api_val = settings.youtube_api_key.get_secret_value()
        if api_val and api_val in text:
            text = text.replace(api_val, "[REDACTED_API_KEY]")
    return text


def get_transcript_client() -> YouTubeTranscriptApi:
    """Instantiates YouTubeTranscriptApi with optional residential proxy."""
    settings = get_settings()
    if settings.transcript_proxy_url:
        proxy_url = settings.transcript_proxy_url.get_secret_value().strip()
        if proxy_url:
            proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
            return YouTubeTranscriptApi(proxy_config=proxy_config)
    return YouTubeTranscriptApi()


def is_block_error(exc: Exception) -> bool:
    """Detects whether an exception indicates IP block, rate limit or captcha."""
    if isinstance(exc, (RequestBlocked, IpBlocked, PoTokenRequired)):
        return True
    if (
        isinstance(exc, HTTPError)
        and getattr(exc, "response", None) is not None
        and exc.response.status_code in (429, 403)
    ):
        return True
    msg = str(exc).lower()
    return any(term in msg for term in ("blocked", "too many requests", "429", "ip blocked", "captcha"))


def is_temporary_error(exc: Exception) -> bool:
    """Detects temporary errors that can be retried with backoff."""
    if is_block_error(exc):
        return False
    if isinstance(exc, (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, VideoUnplayable)):
        return False
    if isinstance(exc, (RequestsConnectionError, Timeout, YouTubeRequestFailed)):
        return True
    if isinstance(exc, HTTPError) and getattr(exc, "response", None) is not None:
        return exc.response.status_code >= 500
    return isinstance(exc, RequestException)


def choose_transcript(
    transcripts: Iterable,
    preferred_languages: Sequence[str] = DEFAULT_TRANSCRIPT_LANGUAGES,
    video_default_language: str | None = None,
):
    """
    Selects the best transcript per R-19:
    1. First preferred language with manual transcript.
    2. First preferred language with auto-generated transcript.
    3. Video's original language (manual first, then auto-generated).
    4. Any available manual transcript.
    5. Any available auto-generated transcript.
    """
    items = list(transcripts)
    if not items:
        return None

    def matches(code: str, target: str) -> bool:
        c = code.lower()
        t = target.lower()
        return c == t or c.split("-")[0] == t

    # 1. Preferred languages, manual
    for pref in preferred_languages:
        for item in items:
            if not item.is_generated and matches(item.language_code, pref):
                return item

    # 2. Preferred languages, auto-generated
    for pref in preferred_languages:
        for item in items:
            if item.is_generated and matches(item.language_code, pref):
                return item

    # 3. Video default language (original upload language)
    if video_default_language:
        for item in items:
            if not item.is_generated and matches(item.language_code, video_default_language):
                return item
        for item in items:
            if item.is_generated and matches(item.language_code, video_default_language):
                return item

    # 4. Any manual transcript
    for item in items:
        if not item.is_generated:
            return item

    # 5. Any auto-generated transcript
    return items[0]


def _sync_fetch_transcript(
    video_id: str,
    preferred_languages: Sequence[str],
    video_default_language: str | None = None,
) -> ExtractedTranscript:
    """Synchronous fetch executed in a thread pool via asyncio.to_thread."""
    api = get_transcript_client()
    transcript_list = api.list(video_id)
    chosen = choose_transcript(
        transcript_list,
        preferred_languages=preferred_languages,
        video_default_language=video_default_language,
    )
    if chosen is None:
        raise NoTranscriptFound(video_id, list(preferred_languages))

    fetched = chosen.fetch()
    raw_snippets = fetched.to_raw_data()
    segments = [
        RawSegment(
            position=idx,
            start_seconds=float(s.get("start", 0.0)),
            duration_seconds=float(s.get("duration", 0.0)),
            text=str(s.get("text", "")).strip(),
        )
        for idx, s in enumerate(raw_snippets)
    ]
    full_text = " ".join(seg.text for seg in segments if seg.text)

    return ExtractedTranscript(
        video_id=video_id,
        language_code=chosen.language_code,
        language_name=chosen.language,
        is_generated=chosen.is_generated,
        full_text=full_text,
        segments=segments,
    )


async def fetch_and_store_video_transcript(
    video_id: str,
    preferred_languages: Sequence[str] | None = None,
    max_attempts: int = DEFAULT_TRANSCRIPT_MAX_ATTEMPTS,
) -> PrismaTranscript:
    """
    Fetches transcript for a single stored video with retry, backoff, and block detection.
    Updates the database transcript and video records.
    """
    video = await database.video.find_unique(where={"id": video_id})
    if not video:
        raise VideoNotFoundError(video_id)

    languages = preferred_languages or DEFAULT_TRANSCRIPT_LANGUAGES
    default_lang = video.defaultLanguage or video.defaultAudioLanguage

    attempts = 0
    last_error_msg: str | None = None

    while attempts < max_attempts:
        attempts += 1
        try:
            extracted = await asyncio.to_thread(_sync_fetch_transcript, video_id, languages, default_lang)
            now = datetime.now(UTC)
            transcript = await database.transcript.upsert(
                where={"videoId": video_id},
                data={
                    "create": {
                        "videoId": video_id,
                        "status": TranscriptStatus.available,
                        "languageCode": extracted.language_code,
                        "languageName": extracted.language_name,
                        "isGenerated": extracted.is_generated,
                        "fullText": extracted.full_text,
                        "segmentCount": len(extracted.segments),
                        "attemptCount": attempts,
                        "lastError": None,
                        "fetchedAt": now,
                    },
                    "update": {
                        "status": TranscriptStatus.available,
                        "languageCode": extracted.language_code,
                        "languageName": extracted.language_name,
                        "isGenerated": extracted.is_generated,
                        "fullText": extracted.full_text,
                        "segmentCount": len(extracted.segments),
                        "attemptCount": attempts,
                        "lastError": None,
                        "fetchedAt": now,
                    },
                },
            )

            await database.transcriptsegment.delete_many(where={"transcriptId": transcript.id})
            if extracted.segments:
                await database.transcriptsegment.create_many(
                    data=[
                        {
                            "transcriptId": transcript.id,
                            "position": seg.position,
                            "startSeconds": seg.start_seconds,
                            "durationSeconds": seg.duration_seconds,
                            "text": seg.text,
                        }
                        for seg in extracted.segments
                    ]
                )

            await database.video.update(
                where={"id": video_id},
                data={"transcriptStatus": TranscriptStatus.available},
            )
            return transcript

        except TranscriptsDisabled as exc:
            now = datetime.now(UTC)
            error_msg = redact_sensitive(str(exc))
            transcript = await database.transcript.upsert(
                where={"videoId": video_id},
                data={
                    "create": {
                        "videoId": video_id,
                        "status": TranscriptStatus.disabled,
                        "attemptCount": attempts,
                        "lastError": error_msg,
                        "fetchedAt": now,
                    },
                    "update": {
                        "status": TranscriptStatus.disabled,
                        "attemptCount": attempts,
                        "lastError": error_msg,
                        "fetchedAt": now,
                    },
                },
            )
            await database.video.update(
                where={"id": video_id},
                data={"transcriptStatus": TranscriptStatus.disabled},
            )
            return transcript

        except NoTranscriptFound as exc:
            now = datetime.now(UTC)
            error_msg = redact_sensitive(str(exc))
            transcript = await database.transcript.upsert(
                where={"videoId": video_id},
                data={
                    "create": {
                        "videoId": video_id,
                        "status": TranscriptStatus.none,
                        "attemptCount": attempts,
                        "lastError": error_msg,
                        "fetchedAt": now,
                    },
                    "update": {
                        "status": TranscriptStatus.none,
                        "attemptCount": attempts,
                        "lastError": error_msg,
                        "fetchedAt": now,
                    },
                },
            )
            await database.video.update(
                where={"id": video_id},
                data={"transcriptStatus": TranscriptStatus.none},
            )
            return transcript

        except Exception as exc:
            sanitized = redact_sensitive(str(exc))
            last_error_msg = sanitized

            if is_block_error(exc):
                now = datetime.now(UTC)
                await database.transcript.upsert(
                    where={"videoId": video_id},
                    data={
                        "create": {
                            "videoId": video_id,
                            "status": TranscriptStatus.blocked,
                            "attemptCount": attempts,
                            "lastError": sanitized,
                            "fetchedAt": now,
                        },
                        "update": {
                            "status": TranscriptStatus.blocked,
                            "attemptCount": attempts,
                            "lastError": sanitized,
                            "fetchedAt": now,
                        },
                    },
                )
                await database.video.update(
                    where={"id": video_id},
                    data={"transcriptStatus": TranscriptStatus.blocked},
                )
                raise TranscriptBlockedError(sanitized) from exc

            if is_temporary_error(exc) and attempts < max_attempts:
                backoff_seconds = 2 ** (attempts - 1)
                logger.warning(
                    "Transcript fetch failed temporarily for %s (attempt %d/%d): %s; retrying in %ds",
                    video_id,
                    attempts,
                    max_attempts,
                    sanitized,
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)
                continue

            break

    # If all attempts exhausted or non-retryable error
    now = datetime.now(UTC)
    transcript = await database.transcript.upsert(
        where={"videoId": video_id},
        data={
            "create": {
                "videoId": video_id,
                "status": TranscriptStatus.failed,
                "attemptCount": attempts,
                "lastError": last_error_msg,
                "fetchedAt": now,
            },
            "update": {
                "status": TranscriptStatus.failed,
                "attemptCount": attempts,
                "lastError": last_error_msg,
                "fetchedAt": now,
            },
        },
    )
    await database.video.update(
        where={"id": video_id},
        data={"transcriptStatus": TranscriptStatus.failed},
    )
    return transcript


async def fetch_and_store_channel_transcripts(
    channel_id: str,
    preferred_languages: Sequence[str] | None = None,
    only_missing: bool = True,
    pause_seconds: float = DEFAULT_TRANSCRIPT_PAUSE_SECONDS,
) -> dict:
    """
    Fetches transcripts for stored videos of a channel.
    Stops immediately if a block is detected (FR-6.9 / R-22), leaving remaining videos pending.
    """
    channel = await database.channel.find_unique(where={"id": channel_id})
    if not channel:
        raise ChannelNotFoundError(channel_id)

    videos = await database.video.find_many(
        where={"channelId": channel_id},
        order={"publishedAt": "desc"},
    )

    targets = [v for v in videos if (not only_missing or v.transcriptStatus != TranscriptStatus.available)]

    total_videos = len(videos)
    processed = 0
    available_cnt = 0
    none_cnt = 0
    disabled_cnt = 0
    failed_cnt = 0
    blocked_cnt = 0
    step_status = "done"

    for idx, vid in enumerate(targets):
        if idx > 0 and pause_seconds > 0:
            await asyncio.sleep(pause_seconds)

        try:
            res = await fetch_and_store_video_transcript(vid.id, preferred_languages)
            processed += 1
            if res.status == TranscriptStatus.available:
                available_cnt += 1
            elif res.status == TranscriptStatus.none:
                none_cnt += 1
            elif res.status == TranscriptStatus.disabled:
                disabled_cnt += 1
            elif res.status == TranscriptStatus.failed:
                failed_cnt += 1
            elif res.status == TranscriptStatus.blocked:
                blocked_cnt += 1
        except TranscriptBlockedError:
            blocked_cnt += 1
            processed += 1
            step_status = "blocked"
            break
        except Exception as e:
            logger.exception("Unexpected error fetching transcript for %s: %s", vid.id, e)
            failed_cnt += 1
            processed += 1

    if step_status != "blocked" and processed < len(targets):
        step_status = "partial"

    return {
        "channel_id": channel_id,
        "total_videos": total_videos,
        "processed": processed,
        "available": available_cnt,
        "none": none_cnt,
        "disabled": disabled_cnt,
        "failed": failed_cnt,
        "blocked": blocked_cnt,
        "step_status": step_status,
    }


async def get_stored_transcript(video_id: str, format_type: str = "segments") -> dict:
    """Retrieves a stored video transcript with its segments or full text."""
    video = await database.video.find_unique(where={"id": video_id})
    if not video:
        raise VideoNotFoundError(video_id)

    include_segments = format_type == "segments"
    transcript = await database.transcript.find_unique(
        where={"videoId": video_id},
        include={"segments": include_segments},
    )
    if not transcript:
        raise TranscriptNotFoundError(video_id)

    segments_data = None
    if include_segments and transcript.segments:
        sorted_segs = sorted(transcript.segments, key=lambda s: s.position)
        segments_data = [
            {
                "position": s.position,
                "start_seconds": s.startSeconds,
                "duration_seconds": s.durationSeconds,
                "text": s.text,
            }
            for s in sorted_segs
        ]

    return {
        "id": transcript.id,
        "video_id": transcript.videoId,
        "status": transcript.status,
        "language_code": transcript.languageCode,
        "language_name": transcript.languageName,
        "is_generated": transcript.isGenerated,
        "full_text": transcript.fullText,
        "segment_count": transcript.segmentCount,
        "attempt_count": transcript.attemptCount,
        "last_error": transcript.lastError,
        "fetched_at": transcript.fetchedAt,
        "segments": segments_data,
    }


async def list_channel_videos_transcript_status(
    channel_id: str,
    status_filter: TranscriptStatus | None = None,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[dict], int]:
    """Lists stored videos of a channel with their transcript status."""
    channel = await database.channel.find_unique(where={"id": channel_id})
    if not channel:
        raise ChannelNotFoundError(channel_id)

    where: dict = {"channelId": channel_id}
    if status_filter:
        where["transcriptStatus"] = status_filter

    total = await database.video.count(where=where)
    videos = await database.video.find_many(
        where=where,
        order={"publishedAt": "desc"},
        skip=skip,
        take=take,
        include={"transcript": True},
    )

    items = []
    for v in videos:
        t = v.transcript
        items.append(
            {
                "video_id": v.id,
                "title": v.title,
                "transcript_status": v.transcriptStatus,
                "language_code": t.languageCode if t else None,
                "is_generated": t.isGenerated if t else None,
                "attempt_count": t.attemptCount if t else 0,
                "last_error": t.lastError if t else None,
                "fetched_at": t.fetchedAt if t else None,
            }
        )

    return items, total
