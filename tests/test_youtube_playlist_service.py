import pytest

from services import youtube_client_service, youtube_playlist_service


@pytest.mark.anyio
async def test_fetch_playlist_items_page(monkeypatch):
    mock_items_res = {
        "nextPageToken": "item_page_2",
        "items": [
            {
                "id": "item1",
                "snippet": {
                    "title": "Public Video 1",
                    "position": 0,
                    "resourceId": {"videoId": "vid1"},
                },
                "status": {"privacyStatus": "public"},
            },
            {
                "id": "item2",
                "snippet": {
                    "title": "Private video",
                    "position": 1,
                    "resourceId": {"videoId": "vid2"},
                },
                "status": {"privacyStatus": "private"},
            },
            {
                "id": "item3",
                "snippet": {
                    "title": "Deleted video",
                    "position": 2,
                    "resourceId": {"videoId": "vid3"},
                },
                "status": {"privacyStatus": "public"},
            },
            {
                # Missing videoId -> skipped
                "id": "item4",
                "snippet": {
                    "title": "Missing video resource",
                    "position": 3,
                    "resourceId": {},
                },
            },
        ],
    }

    async def fake_fetch_playlist_items(playlist_id, **kwargs):
        assert playlist_id == "pl_123"
        return mock_items_res

    saved_items = {}

    async def fake_upsert_item(item_id, playlist_id, record):
        saved_items[item_id] = {"playlistId": playlist_id, **record}
        return record

    monkeypatch.setattr(youtube_client_service, "fetch_playlist_items", fake_fetch_playlist_items)
    monkeypatch.setattr(youtube_playlist_service, "_upsert_playlist_item", fake_upsert_item)

    next_cursor, count, quota = await youtube_playlist_service.fetch_playlist_items_page(
        playlist_id="pl_123",
        cursor="cursor_1",
    )

    assert next_cursor == "item_page_2"
    assert count == 3
    assert quota == 1

    assert "item1" in saved_items
    assert saved_items["item1"]["videoId"] == "vid1"
    assert saved_items["item1"]["position"] == 0
    assert saved_items["item1"]["videoAvailable"] is True

    assert "item2" in saved_items
    assert saved_items["item2"]["videoId"] == "vid2"
    assert saved_items["item2"]["position"] == 1
    assert saved_items["item2"]["videoAvailable"] is False

    assert "item3" in saved_items
    assert saved_items["item3"]["videoId"] == "vid3"
    assert saved_items["item3"]["position"] == 2
    assert saved_items["item3"]["videoAvailable"] is False

    assert "item4" not in saved_items


@pytest.mark.anyio
async def test_fetch_all_playlist_items(monkeypatch):
    pages = [
        ("next_token", 2, 1),
        (None, 1, 1),
    ]

    async def fake_fetch_page(playlist_id, cursor=None):
        return pages.pop(0)

    monkeypatch.setattr(youtube_playlist_service, "fetch_playlist_items_page", fake_fetch_page)

    total_saved, total_quota = await youtube_playlist_service.fetch_all_playlist_items("pl_123")
    assert total_saved == 3
    assert total_quota == 2


@pytest.mark.anyio
async def test_fetch_playlists_page_with_items(monkeypatch):
    mock_playlists_res = {
        "nextPageToken": "pl_page_2",
        "items": [
            {
                "id": "PL_abc",
                "snippet": {
                    "title": "Tutorials",
                    "description": "Tech tutorials",
                    "publishedAt": "2026-01-15T08:00:00Z",
                },
                "contentDetails": {
                    "itemCount": 5,
                },
            }
        ],
    }

    async def fake_fetch_playlists(channel_id, **kwargs):
        assert channel_id == "UC_test"
        return mock_playlists_res

    saved_playlists = {}

    async def fake_upsert_playlist(pl_id, channel_id, record):
        saved_playlists[pl_id] = {"channelId": channel_id, **record}
        return record

    async def fake_fetch_all_items(pl_id):
        assert pl_id == "PL_abc"
        return 5, 2  # 5 items saved, 2 units spent

    monkeypatch.setattr(youtube_client_service, "fetch_playlists", fake_fetch_playlists)
    monkeypatch.setattr(youtube_playlist_service, "_upsert_playlist", fake_upsert_playlist)
    monkeypatch.setattr(youtube_playlist_service, "fetch_all_playlist_items", fake_fetch_all_items)

    next_cursor, count, quota = await youtube_playlist_service.fetch_playlists_page(
        channel_id="UC_test",
        cursor=None,
        fetch_items=True,
    )

    assert next_cursor == "pl_page_2"
    assert count == 1
    assert quota == 3  # 1 for playlist list + 2 for items

    assert "PL_abc" in saved_playlists
    assert saved_playlists["PL_abc"]["channelId"] == "UC_test"
    assert saved_playlists["PL_abc"]["title"] == "Tutorials"
    assert saved_playlists["PL_abc"]["description"] == "Tech tutorials"
    assert saved_playlists["PL_abc"]["itemCount"] == 5
    assert saved_playlists["PL_abc"]["publishedAt"] is not None


@pytest.mark.anyio
async def test_fetch_playlists_page_without_items(monkeypatch):
    mock_playlists_res = {
        "nextPageToken": None,
        "items": [
            {
                "id": "PL_xyz",
                "snippet": {
                    "title": "Vlogs",
                    "publishedAt": "2026-02-10T10:00:00Z",
                },
            }
        ],
    }

    async def fake_fetch_playlists(channel_id, **kwargs):
        return mock_playlists_res

    saved_playlists = {}

    async def fake_upsert_playlist(pl_id, channel_id, record):
        saved_playlists[pl_id] = record
        return record

    monkeypatch.setattr(youtube_client_service, "fetch_playlists", fake_fetch_playlists)
    monkeypatch.setattr(youtube_playlist_service, "_upsert_playlist", fake_upsert_playlist)

    next_cursor, count, quota = await youtube_playlist_service.fetch_playlists_page(
        channel_id="UC_test",
        cursor=None,
        fetch_items=False,
    )

    assert next_cursor is None
    assert count == 1
    assert quota == 1
    assert "PL_xyz" in saved_playlists


def _playlist(pl_id, title):
    return {"id": pl_id, "snippet": {"title": title}, "contentDetails": {"itemCount": 3}}


@pytest.mark.anyio
async def test_fetch_channel_playlists_stops_at_max(monkeypatch):
    from types import SimpleNamespace

    from services import channel_service

    async def fake_fetch_channel(channel_id, force_refresh=False):
        return SimpleNamespace(id=channel_id), 0, True

    calls = []

    async def fake_fetch_playlists(channel_id, page_token=None, max_results=50, **kwargs):
        calls.append(max_results)
        return {"items": [_playlist(f"pl{i}", f"P{i}") for i in range(max_results)], "nextPageToken": "next"}

    async def fake_upsert(pl_id, channel_id, record):
        return SimpleNamespace(id=pl_id, channelId=channel_id, **record)

    monkeypatch.setattr(channel_service, "fetch_channel", fake_fetch_channel)
    monkeypatch.setattr(youtube_client_service, "fetch_playlists", fake_fetch_playlists)
    monkeypatch.setattr(youtube_playlist_service, "_upsert_playlist", fake_upsert)

    result = await youtube_playlist_service.fetch_channel_playlists("UC1", max_playlists=10)

    assert len(result.playlists) == 10
    assert calls == [10]  # one playlists.list call, asking only for 10
    assert result.playlist_videos_saved == 0
    assert result.quota_spent == 1


@pytest.mark.anyio
async def test_fetch_channel_playlists_with_videos_and_new_channel(monkeypatch):
    from types import SimpleNamespace

    from services import channel_service

    async def fake_fetch_channel(channel_id, force_refresh=False):
        return SimpleNamespace(id=channel_id), 1, False  # channel was not stored yet

    async def fake_fetch_playlists(channel_id, page_token=None, max_results=50, **kwargs):
        return {"items": [_playlist("plA", "A"), _playlist("plB", "B")]}

    async def fake_upsert(pl_id, channel_id, record):
        return SimpleNamespace(id=pl_id, channelId=channel_id, **record)

    async def fake_items(playlist_id):
        return 3, 2, 1, 2  # items, details saved, from other channels, quota

    monkeypatch.setattr(channel_service, "fetch_channel", fake_fetch_channel)
    monkeypatch.setattr(youtube_client_service, "fetch_playlists", fake_fetch_playlists)
    monkeypatch.setattr(youtube_playlist_service, "_upsert_playlist", fake_upsert)
    monkeypatch.setattr(youtube_playlist_service, "fetch_playlist_videos_with_details", fake_items)

    result = await youtube_playlist_service.fetch_channel_playlists(
        "UC1", max_playlists=10, include_videos=True
    )

    assert [p.id for p in result.playlists] == [
        "plA",
        "plB",
    ]  # fewer than max: stops when YouTube has no more
    assert result.playlist_videos_saved == 6
    assert result.video_details_saved == 4
    assert result.videos_from_other_channels == 2
    assert result.quota_spent == 1 + 1 + 2 + 2  # channel + playlists page + (items + details) per playlist


@pytest.mark.anyio
async def test_store_videos_by_id_skips_videos_of_unstored_channels(monkeypatch):
    from services import youtube_video_service

    def video(vid, owner):
        return {
            "id": vid,
            "snippet": {"channelId": owner, "title": vid},
            "contentDetails": {"duration": "PT2M"},
        }

    async def fake_fetch_videos(id, **kwargs):
        return {"items": [video(v, "UCmine" if v != "other" else "UCelse") for v in id]}

    async def fake_stored(channel_id):
        return channel_id == "UCmine"

    upserts, gaps = [], []

    async def fake_upsert(vid_id, channel_id, record):
        upserts.append((vid_id, channel_id, record["isShort"]))

    async def fake_gaps(channel_id):
        gaps.append(channel_id)

    async def fake_category(*_args, **_kwargs):
        return None

    monkeypatch.setattr(youtube_client_service, "fetch_videos", fake_fetch_videos)
    monkeypatch.setattr(youtube_video_service, "_channel_is_stored", fake_stored)
    monkeypatch.setattr(youtube_video_service, "_upsert_video", fake_upsert)
    monkeypatch.setattr(youtube_video_service, "update_channel_upload_gaps", fake_gaps)
    monkeypatch.setattr(youtube_video_service, "get_category_name", fake_category)

    ids = [f"v{i}" for i in range(60)] + ["other", "v0"]  # duplicate v0 is fetched once
    saved, skipped, quota = await youtube_video_service.store_videos_by_id(ids)

    assert saved == 60
    assert skipped == 1
    assert quota == 2  # 61 unique IDs = two videos.list batches
    assert upserts[0] == ("v0", "UCmine", True)
    assert gaps == ["UCmine"]
