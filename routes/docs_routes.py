from fastapi import APIRouter

from constants.application_constants import DESIGN_SYSTEM_URL, DOCS_OAUTH2_REDIRECT_URL, DOCS_URL
from controllers import docs_controller

router = APIRouter(include_in_schema=False)

router.add_api_route(DOCS_URL, docs_controller.get_docs_page, methods=["GET"])
router.add_api_route(DOCS_OAUTH2_REDIRECT_URL, docs_controller.get_docs_oauth2_redirect, methods=["GET"])
router.add_api_route(DESIGN_SYSTEM_URL, docs_controller.get_design_system_page, methods=["GET"])
