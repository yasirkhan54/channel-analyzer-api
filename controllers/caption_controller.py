from fastapi import HTTPException

from controllers.video_fetch_controller import as_http_error
from services import youtube_caption_service
from services.youtube_client_service import YouTubeAPIError
from validators.caption_validator import CaptionTrackListResponse, CaptionTrackResponse, FetchCaptionsResponse


async def fetch_video_captions(video_id: str) -> FetchCaptionsResponse:
    try:
        tracks, quota_spent = await youtube_caption_service.fetch_video_captions(video_id)
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchCaptionsResponse(
        video_id=video_id,
        tracks_saved=len(tracks),
        quota_spent=quota_spent,
        tracks=[CaptionTrackResponse.model_validate(track) for track in tracks],
    )


async def list_video_captions(video_id: str) -> CaptionTrackListResponse:
    if not await youtube_caption_service.video_exists(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    tracks = await youtube_caption_service.list_caption_tracks(video_id)
    return CaptionTrackListResponse(
        video_id=video_id, tracks=[CaptionTrackResponse.model_validate(track) for track in tracks]
    )
