from typing import Annotated

from fastapi import HTTPException, Query

from controllers.video_fetch_controller import as_http_error
from services import comment_read_service, youtube_comment_service
from services.youtube_client_service import YouTubeAPIError
from validators.comment_read_validator import (
    CommentListQuery,
    CommentThreadResponse,
    FetchCommentsRequest,
    FetchCommentsResponse,
)
from validators.common_validator import Page


async def list_video_comments(
    video_id: str, query: Annotated[CommentListQuery, Query()]
) -> Page[CommentThreadResponse]:
    if not await comment_read_service.video_exists(video_id):
        raise HTTPException(status_code=404, detail="Video not found")
    threads, total = await comment_read_service.list_comment_threads(video_id, query)
    return Page[CommentThreadResponse](
        items=[CommentThreadResponse.model_validate(thread) for thread in threads],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def fetch_video_comments(video_id: str, request: FetchCommentsRequest) -> FetchCommentsResponse:
    try:
        comments, replies, quota_spent, disabled = await youtube_comment_service.fetch_comments_for_video(
            video_id, request.max_comments, request.include_replies, request.order
        )
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchCommentsResponse(
        video_id=video_id,
        comments_saved=comments,
        replies_saved=replies,
        comments_disabled=disabled,
        quota_spent=quota_spent,
    )
