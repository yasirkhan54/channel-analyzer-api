from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from prisma.enums import FetchJobStatus

from services import fetch_job_service
from validators.common_validator import Page, PageQuery
from validators.fetch_job_validator import (
    CreateFetchJobRequest,
    EstimateFetchJobRequest,
    FetchJobEstimateResponse,
    FetchJobResponse,
)


async def create_fetch_job(body: CreateFetchJobRequest) -> FetchJobResponse:
    try:
        job = await fetch_job_service.create_fetch_job(
            channel_input=body.channel_input,
            comment_mode=body.comment_mode,
            job_type=body.type,
            transcripts_requested=body.transcripts_requested,
        )
        return FetchJobResponse.model_validate(job)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fetch job: {exc}",
        ) from exc


async def get_fetch_job(job_id: int) -> FetchJobResponse:
    try:
        job = await fetch_job_service.get_fetch_job(job_id)
        return FetchJobResponse.model_validate(job)
    except fetch_job_service.JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fetch job not found",
        ) from None


async def list_fetch_jobs(
    query: Annotated[PageQuery, Depends()],
    status_filter: Annotated[
        FetchJobStatus | None,
        Query(alias="status", description="Filter by job status"),
    ] = None,
) -> Page[FetchJobResponse]:
    jobs, total = await fetch_job_service.list_fetch_jobs(
        skip=query.skip,
        take=query.page_size,
        status_filter=status_filter,
    )
    return Page(
        items=[FetchJobResponse.model_validate(j) for j in jobs],
        page=query.page,
        page_size=query.page_size,
        total=total,
    )


async def cancel_fetch_job(job_id: int) -> FetchJobResponse:
    try:
        job = await fetch_job_service.cancel_fetch_job(job_id)
        return FetchJobResponse.model_validate(job)
    except fetch_job_service.JobNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fetch job not found",
        ) from None
    except fetch_job_service.JobAlreadyTerminalError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


async def estimate_fetch_job(body: EstimateFetchJobRequest) -> FetchJobEstimateResponse:
    try:
        data = await fetch_job_service.estimate_fetch_job(
            channel_input=body.channel_input,
            comment_mode=body.comment_mode,
            transcripts_requested=body.transcripts_requested,
        )
        return FetchJobEstimateResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to estimate job quota: {exc}",
        ) from exc
