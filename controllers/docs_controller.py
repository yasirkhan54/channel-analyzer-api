from pathlib import Path

from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse

from constants.application_constants import ASSETS_URL, DOCS_OAUTH2_REDIRECT_URL, OPENAPI_URL, SERVICE_TITLE

DESIGN_SYSTEM_PAGE = Path(__file__).resolve().parent.parent / "public" / "design-system.html"
DOCS_HEAD = (
    f'<link rel="stylesheet" href="{ASSETS_URL}/fonts.css">'
    f'<link rel="stylesheet" href="{ASSETS_URL}/tokens.css">'
    f'<link rel="stylesheet" href="{ASSETS_URL}/docs.css">'
)


async def get_docs_page() -> HTMLResponse:
    """Swagger UI with the design system. Swagger itself is light only, so the page pins the light tokens.

    useUnsafeMarkdown keeps the classes of our own description HTML (SERVICE_DESCRIPTION).
    """
    page = get_swagger_ui_html(
        openapi_url=OPENAPI_URL,
        title=f"{SERVICE_TITLE} - Swagger UI",
        oauth2_redirect_url=DOCS_OAUTH2_REDIRECT_URL,
        swagger_ui_parameters={"useUnsafeMarkdown": True},
    )
    html = bytes(page.body).decode("utf-8")
    html = html.replace("<html>", '<html lang="en" data-theme="light">', 1).replace(
        "</head>", f"{DOCS_HEAD}</head>", 1
    )
    # Live quota-day clock for the info section.
    html = html.replace("</body>", f'<script src="{ASSETS_URL}/docs.js" defer></script></body>', 1)
    return HTMLResponse(html)


async def get_docs_oauth2_redirect() -> HTMLResponse:
    return get_swagger_ui_oauth2_redirect_html()


async def get_design_system_page() -> HTMLResponse:
    return HTMLResponse(DESIGN_SYSTEM_PAGE.read_text(encoding="utf-8"))
