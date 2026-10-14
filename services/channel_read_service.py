from prisma.models import Channel, Video
from prisma.types import VideoWhereInput

from configurations.database_configuration import database
from validators.channel_read_validator import VideoListQuery

# API sort field -> Prisma field. Nullable fields are paged with nulls last (hidden likes, disabled comments).
VIDEO_SORT_FIELDS = {
    "published_at": "publishedAt",
    "view_count": "viewCount",
    "like_count": "likeCount",
    "comment_count": "commentCount",
    "duration_seconds": "durationSeconds",
}
NULLABLE_VIDEO_SORT_FIELDS = frozenset({"viewCount", "likeCount", "commentCount", "durationSeconds"})


async def list_channels(skip: int, take: int) -> tuple[list[Channel], int]:
    channels = await database.channel.find_many(skip=skip, take=take, order=[{"title": "asc"}, {"id": "asc"}])
    return channels, await database.channel.count()


async def get_channel(channel_id: str) -> Channel | None:
    return await database.channel.find_unique(where={"id": channel_id})


async def channel_exists(channel_id: str) -> bool:
    return await database.channel.count(where={"id": channel_id}) > 0


async def get_video(video_id: str) -> Video | None:
    return await database.video.find_unique(where={"id": video_id})


def build_video_filter(channel_id: str, query: VideoListQuery) -> VideoWhereInput:
    where: VideoWhereInput = {"channelId": channel_id}
    if query.is_short is not None:
        where["isShort"] = query.is_short
    published_at = {}
    if query.published_after:
        published_at["gte"] = query.published_after
    if query.published_before:
        published_at["lte"] = query.published_before
    if published_at:
        where["publishedAt"] = published_at
    if query.is_live is True:
        where["OR"] = [{"liveScheduledStartAt": {"not": None}}, {"liveActualStartAt": {"not": None}}]
    elif query.is_live is False:
        where["liveScheduledStartAt"] = None
        where["liveActualStartAt"] = None
    return where


async def list_videos(channel_id: str, query: VideoListQuery) -> tuple[list[Video], int]:
    where = build_video_filter(channel_id, query)
    field = VIDEO_SORT_FIELDS[query.sort_by]
    order = [{field: query.order}, {"id": "asc"}]
    total = await database.video.count(where=where)

    if field not in NULLABLE_VIDEO_SORT_FIELDS:
        videos = await database.video.find_many(
            where=where, order=order, skip=query.skip, take=query.page_size
        )
        return videos, total

    # Prisma Client Python has no "nulls last"; page through the non-null rows first, then the null rows.
    with_value = {"AND": [where, {field: {"not": None}}]}
    without_value = {"AND": [where, {field: None}]}
    with_value_total = await database.video.count(where=with_value)
    videos: list[Video] = []
    if query.skip < with_value_total:
        videos = await database.video.find_many(
            where=with_value, order=order, skip=query.skip, take=query.page_size
        )
    remaining = query.page_size - len(videos)
    if remaining > 0:
        videos += await database.video.find_many(
            where=without_value,
            order=[{"id": "asc"}],
            skip=max(query.skip - with_value_total, 0),
            take=remaining,
        )
    return videos, total
