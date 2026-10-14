from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Query
from prisma.enums import TranscriptStatus

from services import transcript_service
from validators.common_validator import Page, PageQuery
from validators.transcript_validator import (
    ChannelTranscriptsFetchSummary,
    FetchChannelTranscriptsRequest,
    FetchVideoTranscriptRequest,
    TranscriptResponse,
    VideoTranscriptStatusItem,
)


async def fetch_video_transcript(
    video_id: str,
    body: FetchVideoTranscriptRequest | None = None,
) -> TranscriptResponse:
    languages = body.preferred_languages if body else None
    try:
        await transcript_service.fetch_and_store_video_transcript(video_id, preferred_languages=languages)
        data = await transcript_service.get_stored_transcript(video_id, format_type="segments")
        return TranscriptResponse.model_validate(data)
    except transcript_service.VideoNotFoundError:
        raise HTTPException(status_code=404, detail="Video not found") from None
    except transcript_service.TranscriptBlockedError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Transcript fetching blocked by YouTube: {e.reason}",
        ) from e


async def fetch_channel_transcripts(
    channel_id: str,
    body: FetchChannelTranscriptsRequest | None = None,
) -> ChannelTranscriptsFetchSummary:
    languages = body.preferred_languages if body else None
    only_missing = body.only_missing if body else True
    try:
        summary = await transcript_service.fetch_and_store_channel_transcripts(
            channel_id=channel_id,
            preferred_languages=languages,
            only_missing=only_missing,
        )
        return ChannelTranscriptsFetchSummary.model_validate(summary)
    except transcript_service.ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Channel not found") from None


async def get_video_transcript(
    video_id: str,
    format: Annotated[
        Literal["segments", "text"],
        Query(description="Return format: full segments with timestamps or plain text"),
    ] = "segments",
) -> TranscriptResponse:
    try:
        data = await transcript_service.get_stored_transcript(video_id, format_type=format)
        return TranscriptResponse.model_validate(data)
    except transcript_service.VideoNotFoundError:
        raise HTTPException(status_code=404, detail="Video not found") from None
    except transcript_service.TranscriptNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript not found for this video") from None


async def list_channel_transcripts_status(
    channel_id: str,
    query: Annotated[PageQuery, Depends()],
    status: Annotated[
        TranscriptStatus | None,
        Query(description="Filter by transcript status"),
    ] = None,
) -> Page[VideoTranscriptStatusItem]:
    try:
        items, total = await transcript_service.list_channel_videos_transcript_status(
            channel_id=channel_id,
            status_filter=status,
            skip=query.skip,
            take=query.page_size,
        )
        return Page(
            items=[VideoTranscriptStatusItem.model_validate(it) for it in items],
            page=query.page,
            page_size=query.page_size,
            total=total,
        )
    except transcript_service.ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Channel not found") from None
