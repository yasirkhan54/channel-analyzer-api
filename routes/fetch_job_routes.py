from fastapi import APIRouter, Security, status

from constants import route_descriptions
from controllers import fetch_job_controller
from routes.health_routes import client_key_header
from validators.common_validator import ErrorResponse, Page
from validators.fetch_job_validator import (
    FetchJobEstimateResponse,
    FetchJobResponse,
)

router = APIRouter(tags=["Fetch jobs"], dependencies=[Security(client_key_header)])

router.add_api_route(
    "/fetch-jobs",
    fetch_job_controller.create_fetch_job,
    methods=["POST"],
    response_model=FetchJobResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Create a new background channel fetch job",
    description=route_descriptions.CREATE_FETCH_JOB,
)

router.add_api_route(
    "/fetch-jobs",
    fetch_job_controller.list_fetch_jobs,
    methods=["GET"],
    response_model=Page[FetchJobResponse],
    summary="List background fetch jobs",
    description=route_descriptions.LIST_FETCH_JOBS,
)

router.add_api_route(
    "/fetch-jobs/estimate",
    fetch_job_controller.estimate_fetch_job,
    methods=["POST"],
    response_model=FetchJobEstimateResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Estimate quota cost and duration before starting a job",
    description=route_descriptions.ESTIMATE_FETCH_JOB,
)

router.add_api_route(
    "/fetch-jobs/{job_id}",
    fetch_job_controller.get_fetch_job,
    methods=["GET"],
    response_model=FetchJobResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get status and progress of a fetch job",
    description=route_descriptions.GET_FETCH_JOB,
)

router.add_api_route(
    "/fetch-jobs/{job_id}/cancel",
    fetch_job_controller.cancel_fetch_job,
    methods=["POST"],
    response_model=FetchJobResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Cancel a queued, running or paused fetch job",
    description=route_descriptions.CANCEL_FETCH_JOB,
)
