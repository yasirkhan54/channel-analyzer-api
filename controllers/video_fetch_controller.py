from fastapi import HTTPException

from services import youtube_comment_service, youtube_video_service
from services.youtube_client_service import QuotaExhaustedError, ResourceNotFoundError, YouTubeAPIError
from validators.channel_read_validator import VideoResponse
from validators.video_fetch_validator import FetchVideoResponse, FetchVideosRequest, FetchVideosResponse


def as_http_error(exc: YouTubeAPIError) -> HTTPException:
    if isinstance(exc, ResourceNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, QuotaExhaustedError):
        return HTTPException(status_code=429, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


async def fetch_channel_videos(channel_id: str, request: FetchVideosRequest) -> FetchVideosResponse:
    try:
        videos, quota_spent = await youtube_video_service.fetch_channel_videos(channel_id, request.max_videos)
        comments_saved = 0
        if request.comments_per_video:
            for video in videos:
                top, replies, comment_quota, _ = await youtube_comment_service.fetch_video_comments(
                    video.id, request.comments_per_video
                )
                comments_saved += top + replies
                quota_spent += comment_quota
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchVideosResponse(
        channel_id=channel_id,
        videos_saved=len(videos),
        comments_saved=comments_saved,
        quota_spent=quota_spent,
        videos=[VideoResponse.model_validate(video) for video in videos],
    )


async def fetch_video(video_id: str) -> FetchVideoResponse:
    try:
        video, quota_spent = await youtube_video_service.fetch_video(video_id)
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchVideoResponse(quota_spent=quota_spent, video=VideoResponse.model_validate(video))
