from controllers.video_fetch_controller import as_http_error
from services import youtube_category_service
from services.youtube_client_service import YouTubeAPIError
from validators.category_validator import (
    FetchCategoriesRequest,
    FetchCategoriesResponse,
    VideoCategoryResponse,
)


async def fetch_video_categories(request: FetchCategoriesRequest | None = None) -> FetchCategoriesResponse:
    options = request or FetchCategoriesRequest()
    try:
        categories, quota_spent = await youtube_category_service.fetch_video_categories(
            region_code=options.region_code.upper(), language=options.language
        )
    except YouTubeAPIError as exc:
        raise as_http_error(exc) from exc
    return FetchCategoriesResponse(
        categories_saved=len(categories),
        quota_spent=quota_spent,
        categories=[VideoCategoryResponse.model_validate(category) for category in categories],
    )


async def list_video_categories() -> list[VideoCategoryResponse]:
    categories = await youtube_category_service.list_video_categories()
    return [VideoCategoryResponse.model_validate(category) for category in categories]
