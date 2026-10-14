from prisma.models import Channel

from configurations.database_configuration import database

ACTIVE_JOB_STATUSES = ["queued", "running", "paused_for_quota"]


class ChannelBusyError(Exception):
    """The channel has a fetch job that is still queued, running or paused."""


async def has_active_job(channel_id: str) -> bool:
    where = {"channelId": channel_id, "status": {"in": ACTIVE_JOB_STATUSES}}
    return await database.fetchjob.count(where=where) > 0


async def delete_channel(channel_id: str) -> bool:
    """Delete a channel with its videos, comments, playlists, transcripts and search results (FR-10.4).

    Returns False when the channel is not stored. Fetch jobs are kept (their channel link is cleared).
    """
    if await has_active_job(channel_id):
        raise ChannelBusyError
    async with database.tx() as transaction:
        channel = await transaction.channel.find_unique(where={"id": channel_id})
        if channel is None:
            return False
        videos = await transaction.video.find_many(where={"channelId": channel_id})
        await transaction.searchresult.delete_many(
            where={"OR": [{"channelId": channel_id}, {"videoId": {"in": [video.id for video in videos]}}]}
        )
        # Videos, comments, playlists, playlist items and transcripts go with the channel (ON DELETE CASCADE).
        await transaction.channel.delete(where={"id": channel_id})
    return True


async def set_tracked(channel_id: str, tracked: bool) -> Channel | None:
    return await database.channel.update(where={"id": channel_id}, data={"tracked": tracked})
