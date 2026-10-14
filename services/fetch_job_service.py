from typing import Any

from prisma.enums import (
    CommentMode,
    FetchJobStatus,
    FetchJobType,
    TranscriptStepStatus,
)
from prisma.models import FetchJob

from configurations.database_configuration import database
from services import fetch_adapters, fetch_job_runner, quota_service


class JobNotFoundError(Exception):
    def __init__(self, job_id: int):
        super().__init__(f"Fetch job not found: {job_id}")
        self.job_id = job_id


class JobAlreadyTerminalError(Exception):
    def __init__(self, job_id: int, status: str):
        super().__init__(f"Cannot cancel job {job_id} in status: {status}")
        self.job_id = job_id
        self.status = status


async def create_fetch_job(
    channel_input: str,
    comment_mode: CommentMode = CommentMode.top_100,
    job_type: FetchJobType = FetchJobType.full_fetch,
    transcripts_requested: bool | None = None,
) -> FetchJob:
    """Creates a fetch job and queues it for execution (FR-8.1)."""
    t_status = TranscriptStepStatus.not_requested
    t_req = False
    if transcripts_requested is not None:
        t_req = transcripts_requested
        t_status = (
            TranscriptStepStatus.pending if transcripts_requested else TranscriptStepStatus.not_requested
        )

    job = await database.fetchjob.create(
        data={
            "channelInput": channel_input.strip(),
            "commentMode": comment_mode,
            "type": job_type,
            "status": FetchJobStatus.queued,
            "transcriptsRequested": t_req,
            "transcriptStepStatus": t_status,
        }
    )

    fetch_job_runner.trigger_runner()
    return job


async def get_fetch_job(job_id: int) -> FetchJob:
    """Returns status and progress of a fetch job (FR-8.2)."""
    job = await database.fetchjob.find_unique(where={"id": job_id})
    if not job:
        raise JobNotFoundError(job_id)
    return job


async def list_fetch_jobs(
    skip: int = 0,
    take: int = 50,
    status_filter: FetchJobStatus | None = None,
) -> tuple[list[FetchJob], int]:
    """Lists fetch jobs with pagination and optional status filter."""
    where: dict[str, Any] = {}
    if status_filter:
        where["status"] = status_filter

    total = await database.fetchjob.count(where=where)
    jobs = await database.fetchjob.find_many(
        where=where,
        order={"createdAt": "desc"},
        skip=skip,
        take=take,
    )
    return jobs, total


async def cancel_fetch_job(job_id: int) -> FetchJob:
    """Cancels a queued, running, or paused job (FR-8.6)."""
    job = await database.fetchjob.find_unique(where={"id": job_id})
    if not job:
        raise JobNotFoundError(job_id)

    if job.status in (FetchJobStatus.completed, FetchJobStatus.failed, FetchJobStatus.cancelled):
        raise JobAlreadyTerminalError(job_id, job.status)

    updated = await database.fetchjob.update(
        where={"id": job_id},
        data={"status": FetchJobStatus.cancelled},
    )
    return updated


async def estimate_fetch_job(
    channel_input: str,
    comment_mode: CommentMode = CommentMode.top_100,
    transcripts_requested: bool | None = None,
) -> dict[str, Any]:
    """Calculates estimated quota and duration before starting the job (FR-8.8, FR-6.11)."""
    # 1. Check if channel is already stored in DB to avoid any quota for estimation
    q = fetch_adapters.extract_channel_query(channel_input)
    stored_channel = None
    if "channel_id" in q:
        stored_channel = await database.channel.find_unique(where={"id": q["channel_id"]})
    elif "for_handle" in q:
        stored_channel = await database.channel.find_first(where={"customUrl": q["for_handle"]})

    vid_count = stored_channel.videoCount if stored_channel and stored_channel.videoCount else 100
    chan_id = stored_channel.id if stored_channel else None
    chan_title = stored_channel.title if stored_channel else channel_input

    # Transcript default per R-24
    if transcripts_requested is None:
        transcripts_requested = vid_count < 200

    estimate = fetch_adapters.calculate_job_estimate(
        video_count=vid_count,
        comment_mode=comment_mode,
        transcripts_requested=transcripts_requested,
    )

    quota_status = await quota_service.get_quota_status()
    quota_available = await quota_service.check_quota_available(cost=estimate["estimated_quota_units_min"])

    warning = None
    if "for_custom_url" in q:
        warning = "Legacy /c/ custom URL requires 100 units search to resolve (FR-1.5)."

    return {
        "channel_id": chan_id,
        "channel_title": chan_title,
        "video_count": vid_count,
        "comment_mode": comment_mode,
        "estimated_quota_units_min": estimate["estimated_quota_units_min"],
        "estimated_quota_units_max": estimate["estimated_quota_units_max"],
        "transcripts_requested": transcripts_requested,
        "estimated_transcript_time_seconds": estimate["estimated_transcript_time_seconds"],
        "estimated_transcript_time_formatted": estimate["estimated_transcript_time_formatted"],
        "quota_available": quota_available,
        "current_quota_remaining": quota_status["units_remaining"],
        "warning": warning,
    }
