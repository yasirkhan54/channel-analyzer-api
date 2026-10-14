from prisma.models import Playlist, PlaylistItem, Video

from configurations.database_configuration import database


async def playlist_exists(playlist_id: str) -> bool:
    return await database.playlist.count(where={"id": playlist_id}) > 0


async def list_playlists(channel_id: str, skip: int, take: int) -> tuple[list[Playlist], int]:
    where = {"channelId": channel_id}
    playlists = await database.playlist.find_many(
        where=where, order=[{"title": "asc"}, {"id": "asc"}], skip=skip, take=take
    )
    return playlists, await database.playlist.count(where=where)


async def list_playlist_items(
    playlist_id: str, skip: int, take: int
) -> tuple[list[tuple[PlaylistItem, Video | None]], int]:
    """Playlist items in position order, each paired with its stored video (video ID is not a foreign key)."""
    where = {"playlistId": playlist_id}
    items = await database.playlistitem.find_many(
        where=where, order=[{"position": "asc"}, {"id": "asc"}], skip=skip, take=take
    )
    videos = await database.video.find_many(where={"id": {"in": [item.videoId for item in items]}})
    videos_by_id = {video.id: video for video in videos}
    pairs = [(item, videos_by_id.get(item.videoId)) for item in items]
    return pairs, await database.playlistitem.count(where=where)
