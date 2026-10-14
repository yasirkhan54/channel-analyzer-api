from prisma.models import Comment
from prisma.types import CommentWhereInput

from configurations.database_configuration import database
from validators.comment_read_validator import CommentListQuery

COMMENT_SORT_FIELDS = {"like_count": "likeCount", "published_at": "publishedAt"}


async def video_exists(video_id: str) -> bool:
    return await database.video.count(where={"id": video_id}) > 0


async def list_comment_threads(video_id: str, query: CommentListQuery) -> tuple[list[Comment], int]:
    """Top-level comments of a video, each with all its stored replies (oldest first)."""
    where: CommentWhereInput = {"videoId": video_id, "parentId": None}
    threads = await database.comment.find_many(
        where=where,
        order=[{COMMENT_SORT_FIELDS[query.sort_by]: query.order}, {"id": "asc"}],
        skip=query.skip,
        take=query.page_size,
        include={"replies": {"order_by": [{"publishedAt": "asc"}, {"id": "asc"}]}},
    )
    return threads, await database.comment.count(where=where)
