import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from prisma.enums import (
    CommentMode,
    FetchJobStage,
    FetchJobStatus,
    TranscriptStatus,
    TranscriptStepStatus,
)

from prisma import Json
from services import fetch_adapters, quota_service, transcript_service
from services.youtube_client_service import QuotaExhaustedError, ResourceNotFoundError, YouTubeRequestError

logger = logging.getLogger(__name__)

# Enforce strictly one running background job at a time (R-16, FR-8.7)
_runner_lock = asyncio.Lock()


async def is_job_cancelled(job_id: int) -> bool:
    from configurations.database_configuration import database

    job = await database.fetchjob.find_unique(where={"id": job_id})
    return job is None or job.status == FetchJobStatus.cancelled


async def execute_job(job_id: int) -> None:
    from configurations.database_configuration import database

    job = await database.fetchjob.find_unique(where={"id": job_id})
    if not job or job.status in (FetchJobStatus.completed, FetchJobStatus.cancelled, FetchJobStatus.failed):
        return

    # Check quota availability before starting
    has_quota = await quota_service.check_quota_available(cost=2)
    if not has_quota:
        await database.fetchjob.update(
            where={"id": job_id},
            data={
                "status": FetchJobStatus.paused_for_quota,
                "errorDetail": "Paused for quota limit or safety margin",
            },
        )
        return

    # Mark running
    started_at = job.startedAt or datetime.now(UTC)
    await database.fetchjob.update(
        where={"id": job_id},
        data={
            "status": FetchJobStatus.running,
            "startedAt": started_at,
            "errorDetail": None,
        },
    )

    cursor_data: dict[str, Any] = job.resumeCursor if isinstance(job.resumeCursor, dict) else {}

    try:
        # 1. CHANNEL RESOLUTION & DETAILS
        chan_id = job.channelId
        uploads_id = cursor_data.get("uploads_playlist_id")

        if not chan_id or not uploads_id:
            await database.fetchjob.update(
                where={"id": job_id},
                data={"stage": FetchJobStage.channel},
            )
            chan_info = await fetch_adapters.resolve_and_fetch_channel(job.channelInput)
            chan_id = chan_info["id"]
            uploads_id = chan_info["uploads_playlist_id"]
            vid_count = chan_info["video_count"]

            transcripts_req = job.transcriptsRequested
            t_status = job.transcriptStepStatus
            if (
                not transcripts_req
                and job.type == "full_fetch"
                and t_status == TranscriptStepStatus.not_requested
            ):
                # Per R-24: On by default for channels under 200 videos, off for 200+
                transcripts_req = vid_count < 200
                t_status = (
                    TranscriptStepStatus.pending if transcripts_req else TranscriptStepStatus.not_requested
                )

            cursor_data["uploads_playlist_id"] = uploads_id
            cursor_data["stage"] = "channel_done"

            await database.fetchjob.update(
                where={"id": job_id},
                data={
                    "channelId": chan_id,
                    "videosFound": vid_count,
                    "transcriptsRequested": transcripts_req,
                    "transcriptStepStatus": t_status,
                    "quotaSpent": {"increment": 1},
                    "resumeCursor": Json(cursor_data),
                },
            )

        if await is_job_cancelled(job_id):
            return

        # 2. VIDEOS DISCOVERY & DETAILS
        if cursor_data.get("stage") in ("channel_done", "videos"):
            await database.fetchjob.update(
                where={"id": job_id},
                data={"stage": FetchJobStage.videos},
            )
            video_cursor = cursor_data.get("videos_page_token")

            while True:
                if await is_job_cancelled(job_id):
                    return

                if not await quota_service.check_quota_available(cost=2):
                    raise QuotaExhaustedError("Quota exhausted during videos fetch")

                next_token, count, cost = await fetch_adapters.fetch_videos_page(
                    channel_id=chan_id,
                    uploads_playlist_id=uploads_id,
                    cursor=video_cursor,
                )

                cursor_data["stage"] = "videos"
                cursor_data["videos_page_token"] = next_token

                await database.fetchjob.update(
                    where={"id": job_id},
                    data={
                        "videosDone": {"increment": count},
                        "quotaSpent": {"increment": cost},
                        "resumeCursor": Json(cursor_data),
                    },
                )

                if not next_token:
                    cursor_data["stage"] = "videos_done"
                    cursor_data.pop("videos_page_token", None)
                    await database.fetchjob.update(
                        where={"id": job_id},
                        data={"resumeCursor": Json(cursor_data)},
                    )
                    break
                video_cursor = next_token

        if await is_job_cancelled(job_id):
            return

        # 3. COMMENTS: every stored video, one comment page at a time (top_100 = one page, all = every page)
        if cursor_data.get("stage") in ("videos_done", "comments"):
            if job.commentMode != CommentMode.skip:
                await database.fetchjob.update(where={"id": job_id}, data={"stage": FetchJobStage.comments})
                vids = await database.video.find_many(
                    where={"channelId": chan_id}, order=[{"publishedAt": "desc"}, {"id": "asc"}]
                )
                c_idx = cursor_data.get("comment_video_index", 0)
                comment_cursor = cursor_data.get("comment_page_token")

                while c_idx < len(vids):
                    target_vid = vids[c_idx]
                    # A count of 0 means there is nothing to fetch; skip it and save the unit.
                    if target_vid.commentCount != 0:
                        if await is_job_cancelled(job_id):
                            return
                        try:
                            comment_cursor, count, cost = await fetch_adapters.fetch_comments_page(
                                target_vid.id, job.commentMode, comment_cursor
                            )
                        except (ResourceNotFoundError, YouTubeRequestError) as exc:
                            # A private, deleted or restricted video must not fail the whole job.
                            logger.warning(
                                "Skipping comments of %s in job %d: %s", target_vid.id, job_id, exc
                            )
                            comment_cursor, count, cost = None, 0, 1
                        await database.fetchjob.update(
                            where={"id": job_id},
                            data={"commentsFetched": {"increment": count}, "quotaSpent": {"increment": cost}},
                        )
                    else:
                        comment_cursor = None

                    if not comment_cursor:
                        c_idx += 1
                    cursor_data["stage"] = "comments"
                    cursor_data["comment_video_index"] = c_idx
                    cursor_data["comment_page_token"] = comment_cursor
                    await database.fetchjob.update(
                        where={"id": job_id}, data={"resumeCursor": Json(cursor_data)}
                    )

            cursor_data["stage"] = "comments_done"
            cursor_data.pop("comment_video_index", None)
            cursor_data.pop("comment_page_token", None)
            await database.fetchjob.update(where={"id": job_id}, data={"resumeCursor": Json(cursor_data)})

        if await is_job_cancelled(job_id):
            return

        # 4. PLAYLISTS: every channel playlist with all its items, one page of 50 playlists at a time
        if cursor_data.get("stage") in ("comments_done", "playlists"):
            await database.fetchjob.update(where={"id": job_id}, data={"stage": FetchJobStage.playlists})
            playlist_cursor = cursor_data.get("playlists_page_token")
            while True:
                if await is_job_cancelled(job_id):
                    return
                playlist_cursor, count, cost = await fetch_adapters.fetch_playlists_page(
                    chan_id, playlist_cursor
                )
                cursor_data["stage"] = "playlists"
                cursor_data["playlists_page_token"] = playlist_cursor
                await database.fetchjob.update(
                    where={"id": job_id},
                    data={
                        "playlistsDone": {"increment": count},
                        "quotaSpent": {"increment": cost},
                        "resumeCursor": Json(cursor_data),
                    },
                )
                if not playlist_cursor:
                    break

            cursor_data["stage"] = "playlists_done"
            cursor_data.pop("playlists_page_token", None)
            await database.fetchjob.update(where={"id": job_id}, data={"resumeCursor": Json(cursor_data)})

        if await is_job_cancelled(job_id):
            return

        # 5. TRANSCRIPTS: only when requested; no quota cost
        if cursor_data.get("stage") in ("playlists_done", "transcripts"):
            current = await database.fetchjob.find_unique(where={"id": job_id})
            if current and current.transcriptsRequested:
                await database.fetchjob.update(
                    where={"id": job_id},
                    data={
                        "stage": FetchJobStage.transcripts,
                        "transcriptStepStatus": TranscriptStepStatus.running,
                    },
                )
                vids = await database.video.find_many(
                    where={"channelId": chan_id}, order=[{"publishedAt": "desc"}, {"id": "asc"}]
                )
                t_idx = cursor_data.get("transcript_video_index", 0)
                is_blocked = False

                while t_idx < len(vids):
                    if await is_job_cancelled(job_id):
                        return

                    target_vid = vids[t_idx]
                    try:
                        res = await transcript_service.fetch_and_store_video_transcript(target_vid.id)
                        counter = (
                            "transcriptsDone"
                            if res.status == TranscriptStatus.available
                            else "transcriptsMissing"
                        )
                        await database.fetchjob.update(where={"id": job_id}, data={counter: {"increment": 1}})
                    except transcript_service.TranscriptBlockedError:
                        is_blocked = True
                        await database.fetchjob.update(
                            where={"id": job_id},
                            data={
                                "transcriptsBlocked": {"increment": 1},
                                "transcriptStepStatus": TranscriptStepStatus.blocked,
                            },
                        )
                        logger.warning(
                            "YouTube blocked transcript requests for job %d. Stopping transcript stage.",
                            job_id,
                        )
                        break
                    except Exception as e:
                        logger.exception("Error fetching transcript for %s: %s", target_vid.id, e)
                        await database.fetchjob.update(
                            where={"id": job_id},
                            data={"transcriptsMissing": {"increment": 1}},
                        )

                    t_idx += 1
                    cursor_data["stage"] = "transcripts"
                    cursor_data["transcript_video_index"] = t_idx
                    await database.fetchjob.update(
                        where={"id": job_id},
                        data={"resumeCursor": Json(cursor_data)},
                    )
                    await asyncio.sleep(0.5)

                if not is_blocked:
                    await database.fetchjob.update(
                        where={"id": job_id},
                        data={"transcriptStepStatus": TranscriptStepStatus.done},
                    )

        # 6. JOB COMPLETED
        await database.fetchjob.update(
            where={"id": job_id},
            data={
                "status": FetchJobStatus.completed,
                "finishedAt": datetime.now(UTC),
                "resumeCursor": Json(None),
            },
        )
        logger.info("FetchJob %d completed successfully.", job_id)

    except QuotaExhaustedError as exc:
        logger.warning("FetchJob %d paused for quota: %s", job_id, exc)
        await database.fetchjob.update(
            where={"id": job_id},
            data={
                "status": FetchJobStatus.paused_for_quota,
                "errorDetail": str(exc),
                "resumeCursor": Json(cursor_data),
            },
        )
    except Exception as exc:
        logger.exception("FetchJob %d failed: %s", job_id, exc)
        await database.fetchjob.update(
            where={"id": job_id},
            data={
                "status": FetchJobStatus.failed,
                "errorDetail": str(exc),
                "finishedAt": datetime.now(UTC),
            },
        )


async def run_worker() -> None:
    """Continuously processes queued or paused fetch jobs in FIFO queue order (R-16, FR-8.7)."""
    from configurations.database_configuration import database

    async with _runner_lock:
        while True:
            # 1. Look for queued jobs
            job = await database.fetchjob.find_first(
                where={"status": FetchJobStatus.queued},
                order={"createdAt": "asc"},
            )
            # 2. Or resume paused jobs if quota reset
            if not job:
                has_quota = await quota_service.check_quota_available(cost=5)
                if has_quota:
                    job = await database.fetchjob.find_first(
                        where={"status": FetchJobStatus.paused_for_quota},
                        order={"createdAt": "asc"},
                    )

            if not job:
                break

            await execute_job(job.id)


RESUME_CHECK_INTERVAL_SECONDS = 10 * 60


async def run_schedule() -> None:
    """Restart jobs cut off by a shutdown, then keep checking for paused jobs to resume (FR-8.3, FR-8.4).

    A job still marked running at startup was interrupted, so it goes back to the queue and continues
    from its saved cursor. Paused jobs restart once the quota resets at midnight Pacific time.
    """
    from configurations.database_configuration import database

    await database.fetchjob.update_many(
        where={"status": FetchJobStatus.running}, data={"status": FetchJobStatus.queued}
    )
    while True:
        try:
            await run_worker()
        except Exception:
            logger.exception("Fetch job worker failed")
        await asyncio.sleep(RESUME_CHECK_INTERVAL_SECONDS)


def trigger_runner() -> None:
    """Spawns background runner task if not already executing."""
    asyncio.create_task(run_worker())
