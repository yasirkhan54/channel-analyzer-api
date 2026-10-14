from datetime import UTC, datetime
from typing import Any

from configurations.database_configuration import database
from services import youtube_client_service, youtube_video_service


def parse_rfc3339_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


async def _upsert_comment(comment_id: str, record: dict[str, Any]) -> Any:
    return await database.comment.upsert(
        where={"id": comment_id},
        data={
            "create": {
                "id": comment_id,
                **record,
            },
            "update": {k: v for k, v in record.items() if k != "videoId"},
        },
    )


async def _fetch_remaining_replies(
    parent_id: str,
    video_id: str,
    already_saved_ids: set[str],
) -> tuple[int, int]:
    """Fetch additional replies for a thread when more exist than returned inline (R-5)."""
    reply_cursor: str | None = None
    saved_count = 0
    quota_spent = 0
    now = datetime.now(UTC)

    while True:
        try:
            res = await youtube_client_service.fetch_comments(
                parent_id=parent_id,
                max_results=100,
                page_token=reply_cursor,
            )
            quota_spent += 1
        except Exception:
            break

        items = res.get("items", [])
        for rep in items:
            rep_id = rep.get("id")
            if not rep_id or rep_id in already_saved_ids:
                continue

            snip = rep.get("snippet", {})
            author_chan = snip.get("authorChannelId", {})
            author_chan_id = author_chan.get("value") if isinstance(author_chan, dict) else None

            await _upsert_comment(
                rep_id,
                {
                    "videoId": video_id,
                    "parentId": parent_id,
                    "text": snip.get("textDisplay", ""),
                    "authorDisplayName": snip.get("authorDisplayName"),
                    "authorChannelId": author_chan_id,
                    "likeCount": int(snip.get("likeCount", 0)),
                    "publishedAt": parse_rfc3339_datetime(snip.get("publishedAt")) or now,
                    "editedAt": parse_rfc3339_datetime(snip.get("updatedAt")),
                    "fetchedAt": now,
                },
            )
            already_saved_ids.add(rep_id)
            saved_count += 1

        reply_cursor = res.get("nextPageToken")
        if not reply_cursor:
            break

    return saved_count, quota_spent


def _comment_record(
    snip: dict[str, Any], video_id: str, parent_id: str | None, now: datetime
) -> dict[str, Any]:
    author_chan = snip.get("authorChannelId", {})
    return {
        "videoId": video_id,
        "parentId": parent_id,
        "text": snip.get("textDisplay", ""),
        "authorDisplayName": snip.get("authorDisplayName"),
        "authorChannelId": author_chan.get("value") if isinstance(author_chan, dict) else None,
        "likeCount": int(snip.get("likeCount", 0)),
        "publishedAt": parse_rfc3339_datetime(snip.get("publishedAt")) or now,
        "editedAt": parse_rfc3339_datetime(snip.get("updatedAt")),
        "fetchedAt": now,
    }


async def _save_thread(
    thread: dict[str, Any], video_id: str, now: datetime, include_replies: bool
) -> tuple[int, int, int]:
    """Store one comment thread: the top-level comment and, optionally, all its replies (R-5).

    Returns (top_level_saved, replies_saved, extra_quota_spent).
    """
    thread_snip = thread.get("snippet", {})
    top = thread_snip.get("topLevelComment", {})
    comment_id = top.get("id")
    if not comment_id:
        return 0, 0, 0

    total_reply_count = int(thread_snip.get("totalReplyCount", 0))
    record = _comment_record(top.get("snippet", {}), video_id, None, now)
    await _upsert_comment(comment_id, {**record, "totalReplyCount": total_reply_count})
    if not include_replies:
        return 1, 0, 0

    saved_reply_ids: set[str] = set()
    for rep in thread.get("replies", {}).get("comments", []):
        rep_id = rep.get("id")
        if not rep_id:
            continue
        await _upsert_comment(rep_id, _comment_record(rep.get("snippet", {}), video_id, comment_id, now))
        saved_reply_ids.add(rep_id)

    replies_saved = len(saved_reply_ids)
    extra_quota = 0
    # R-5: If thread has more replies than returned inline, fetch them with comments.list
    if total_reply_count > replies_saved:
        extra_count, extra_quota = await _fetch_remaining_replies(
            parent_id=comment_id,
            video_id=video_id,
            already_saved_ids=saved_reply_ids,
        )
        replies_saved += extra_count
    return 1, replies_saved, extra_quota


async def fetch_comments_page(
    video_id: str,
    mode: str = "top_100",
    cursor: str | None = None,
) -> tuple[str | None, int, int]:
    """Fetch one page of comments and all their replies for a video (FR-4.1 to FR-4.4, R-5, R-23).

    Modes:
    - "skip": skips comments entirely (0 quota, 0 comments)
    - "top_100": fetches top 100 top-level comments by relevance with all replies (1 thread page)
    - "all": paginates through all top-level comments and all replies

    Returns (next_cursor, total_comments_saved, quota_spent).
    """
    if mode == "skip":
        return None, 0, 0

    try:
        threads_res = await youtube_client_service.fetch_comment_threads(
            video_id=video_id,
            order="relevance",
            max_results=100,
            page_token=cursor,
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "disabled" in msg or "commentsdisabled" in msg:
            # FR-4.3: Record comments-disabled videos and continue without failing
            return None, 0, 1
        raise

    items = threads_res.get("items", [])
    now = datetime.now(UTC)
    total_saved = 0
    quota_spent = 1  # 1 unit for commentThreads.list

    for it in items:
        top_saved, replies_saved, reply_quota = await _save_thread(it, video_id, now, include_replies=True)
        total_saved += top_saved + replies_saved
        quota_spent += reply_quota

    # Next cursor: None for top_100 (single page of 100), or nextPageToken for "all" mode
    next_cursor = threads_res.get("nextPageToken") if mode == "all" else None
    return next_cursor, total_saved, quota_spent


def _comments_disabled(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "disabled" in msg or "commentsdisabled" in msg


async def fetch_video_comments(
    video_id: str,
    max_comments: int,
    include_replies: bool = True,
    order: str = "relevance",
) -> tuple[int, int, int, bool]:
    """Fetch up to max_comments top-level comments of a stored video, optionally with all their replies.

    commentThreads.list returns up to 100 per unit; replies beyond those returned inline cost 1 unit per
    100 per thread. Returns (comments_saved, replies_saved, quota_spent, comments_disabled).
    """
    saved_top = saved_replies = quota_spent = 0
    cursor: str | None = None
    now = datetime.now(UTC)

    while saved_top < max_comments:
        remaining = max_comments - saved_top
        try:
            res = await youtube_client_service.fetch_comment_threads(
                video_id=video_id,
                order=order,
                max_results=min(100, remaining),
                page_token=cursor,
            )
        except Exception as exc:
            if _comments_disabled(exc):
                return saved_top, saved_replies, quota_spent, True
            raise
        quota_spent += 1

        for thread in res.get("items", [])[:remaining]:
            top, replies, extra = await _save_thread(thread, video_id, now, include_replies)
            saved_top += top
            saved_replies += replies
            quota_spent += extra
        cursor = res.get("nextPageToken")
        if not cursor:
            break

    return saved_top, saved_replies, quota_spent, False


async def _video_is_stored(video_id: str) -> bool:
    return await database.video.find_unique(where={"id": video_id}) is not None


async def fetch_comments_for_video(
    video_id: str,
    max_comments: int,
    include_replies: bool = True,
    order: str = "relevance",
) -> tuple[int, int, int, bool]:
    """Like fetch_video_comments, but stores the video (and its channel) first when it is missing."""
    quota_spent = 0
    if not await _video_is_stored(video_id):
        _, quota_spent = await youtube_video_service.fetch_video(video_id)
    comments, replies, comment_quota, disabled = await fetch_video_comments(
        video_id, max_comments, include_replies, order
    )
    return comments, replies, quota_spent + comment_quota, disabled
