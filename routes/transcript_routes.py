from fastapi import APIRouter, Security

from constants import route_descriptions
from controllers import transcript_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse, Page
from validators.transcript_validator import (
    ChannelTranscriptsFetchSummary,
    TranscriptResponse,
    VideoTranscriptStatusItem,
)

router = APIRouter(tags=["Transcripts"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/videos/{video_id}/transcript",
    transcript_controller.fetch_video_transcript,
    methods=["POST"],
    response_model=TranscriptResponse,
    responses={
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="Fetch and store transcript for a video",
    description=route_descriptions.FETCH_VIDEO_TRANSCRIPT,
)

router.add_api_route(
    "/videos/{video_id}/transcript",
    transcript_controller.get_video_transcript,
    methods=["GET"],
    response_model=TranscriptResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get a stored video transcript",
    description=route_descriptions.GET_VIDEO_TRANSCRIPT,
)

router.add_api_route(
    "/channels/{channel_id}/transcripts",
    transcript_controller.fetch_channel_transcripts,
    methods=["POST"],
    response_model=ChannelTranscriptsFetchSummary,
    responses={404: {"model": ErrorResponse}},
    summary="Fetch transcripts for stored videos of a channel",
    description=route_descriptions.FETCH_CHANNEL_TRANSCRIPTS,
)

router.add_api_route(
    "/channels/{channel_id}/transcripts/status",
    transcript_controller.list_channel_transcripts_status,
    methods=["GET"],
    response_model=Page[VideoTranscriptStatusItem],
    responses={404: {"model": ErrorResponse}},
    summary="List a channel's videos with their transcript status",
    description=route_descriptions.LIST_CHANNEL_TRANSCRIPT_STATUS,
)
