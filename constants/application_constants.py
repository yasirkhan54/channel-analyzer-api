SERVICE_NAME = "channel-analyzer-api"
SERVICE_VERSION = "0.1.0"
SERVICE_TITLE = "YouTube Channel Analyzer API"
# Rendered by Swagger UI as one HTML block (useUnsafeMarkdown keeps its classes), styled by
# public/docs-theme.css.
# Keep it flush left with no blank lines: Markdown would turn indented or separated lines into code blocks.
SERVICE_DESCRIPTION = """<div class="ytca">
<header class="ytca-head">
<div class="ytca-avatar"><svg viewBox="0 0 30 22" aria-hidden="true"><rect x="1" y="13" width="7" height="8"
rx="2" fill="#0F0F0F"/><rect x="11.5" y="7" width="7" height="14" rx="2" fill="#0F0F0F"/><rect x="22" y="1"
width="7" height="20" rx="2" fill="#FF0033"/></svg></div>
<div class="ytca-id">
<h1>Channel Analyzer API</h1>
<p class="ytca-meta"><b>@localhost:8010</b><i>·</i><span>v0.1.0</span><i>·</i><span>OpenAPI
3.1</span><i>·</i><span>10,000 units a day</span></p>
<p class="ytca-desc">Fetch a channel once, read it at zero quota. Every route below is live; reads from
storage never spend quota.</p>
</div>
<div class="ytca-actions">
<a class="pill pill-primary" href="#/Fetch%20jobs">Start a fetch job</a>
<a class="pill" href="/" target="_self">Home page</a>
<a class="pill" href="/api-docs/openapi.json" target="_blank">OpenAPI JSON</a>
<a class="pill" href="/health" target="_blank">Health</a>
</div>
</header>
<nav class="ytca-chips" aria-label="Jump to a group">
<a class="chip" href="#/Fetch%20jobs">Fetch jobs</a>
<a class="chip" href="#/Channels">Channels</a>
<a class="chip" href="#/Videos">Videos</a>
<a class="chip" href="#/Comments">Comments</a>
<a class="chip" href="#/Playlists">Playlists</a>
<a class="chip" href="#/Transcripts">Transcripts</a>
<a class="chip" href="#/Captions">Captions</a>
<a class="chip" href="#/Channel%20sections">Channel sections</a>
<a class="chip" href="#/Search">Search</a>
<a class="chip" href="#/Quota">Quota</a>
</nav>
<div class="ytca-cols">
<section class="ytca-col">
<h2>How a fetch runs</h2>
<ol class="ytca-flow">
<li><div class="ytca-step-head"><b>Estimate the cost</b><span class="ytca-note">free</span></div><a
class="ytca-route" href="#/Fetch%20jobs"><span class="method
method-post">POST</span><code>/fetch-jobs/estimate</code></a><p>See the quota range before spending
anything.</p></li>
<li><div class="ytca-step-head"><b>Start the job</b><span class="ytca-note">returns at once</span></div><a
class="ytca-route" href="#/Fetch%20jobs"><span class="method
method-post">POST</span><code>/fetch-jobs</code></a><p>Send a URL, @handle or ID. The job ID comes back at
once.</p></li>
<li><div class="ytca-step-head"><b>Follow, pause, resume</b><span class="ytca-note">resumable</span></div><a
class="ytca-route" href="#/Fetch%20jobs"><span class="method
method-get">GET</span><code>/fetch-jobs/{job_id}</code></a><p>Out of units, it keeps its cursor and carries
on after the reset.</p></li>
<li><div class="ytca-step-head"><b>Read from storage</b><span class="ytca-note">free</span></div><a
class="ytca-route" href="#/Fetch%20jobs"><span class="method
method-get">GET</span><code>/channels</code></a><p>Channels, videos, comments, playlists,
transcripts.</p></li>
</ol>
</section>
<section class="ytca-col ytca-quota">
<h2>Quota today</h2>
<p class="ytca-clock"><span class="ytca-count">--:--:--</span><span class="ytca-reset-at">until reset at
midnight Pacific</span></p>
<div class="ytca-day" role="progressbar" aria-label="Quota day elapsed" aria-valuemin="0"
aria-valuemax="100"><span></span></div>
<p class="ytca-day-legend"><span>reset</span><span>10,000 units, 200 held back</span><span>reset</span></p>
<ul class="ytca-ladder">
<li><b class="free">0</b><span>Reading anything stored, and transcripts</span></li>
<li><b>1</b><span>A list page (50 videos, 100 comments, 50 playlists) or a channel lookup</span></li>
<li><b class="high">50</b><span>Caption track list, per video</span></li>
<li><b class="high">100</b><span>Keyword search page, or a legacy /c/ URL</span></li>
</ul>
<p class="ytca-small">Live usage: <code>GET /quota</code></p>
</section>
<section class="ytca-col">
<h2>Authorize</h2>
<ol class="ytca-auth">
<li>Click <b>Authorize</b>, just below on the right.</li>
<li>Paste only the value of <code>CLIENT_API_KEY</code> from <code>.env</code>.</li>
<li>It is sent as <code>X-API-Key</code>. Open without it: <code>/</code>, <code>/health</code>, these docs,
<code>/design-system</code>.</li>
</ol>
<p class="ytca-limit"><b>60</b> requests a minute per key, then <code>429</code></p>
<h2 class="ytca-h2-gap">House rules</h2>
<ul class="ytca-rules">
<li><b>Kept until you delete it.</b> Refresh a channel to update it.</li>
<li><b>Public data only.</b> Nothing is written to YouTube.</li>
<li><b>Secrets stay on the server.</b> The Google key never leaves it.</li>
</ul>
</section>
</div>
<section class="ytca-store">
<h2>What it stores <span>A channel's whole public record in one Postgres store</span></h2>
<ul>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="4"/><path
d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg></span><div><b>Channel</b><span class="ytca-cost">1
unit</span><p>Name, handle, country, totals, keywords, topics.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18"
height="14" rx="3"/><path d="M8 19v2M16 19v2"/></svg></span><div><b>Videos</b><span class="ytca-cost">2 per
50</span><p>Stats, duration, category, captions, live details, Shorts flag.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 15a2 2 0 0 1-2 2H8l-4
4V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z"/></svg></span><div><b>Comments</b><span class="ytca-cost">1 per
100</span><p>Top 100 per video with every reply; all or none per job.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h12M4 11h12M4 16h7M15
15l5-3v8z"/></svg></span><div><b>Playlists</b><span class="ytca-cost">1 per 50</span><p>Every playlist with
its videos in order.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 11h16M4
16h10"/></svg></span><div><b>Transcripts</b><span class="ytca-cost">free</span><p>Timed segments and full
text: English, Urdu, Hindi.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18"
height="14" rx="3"/><path d="M10 10.5a2 2 0 1 0 0 3M17 10.5a2 2 0 1 0 0
3"/></svg></span><div><b>Captions</b><span class="ytca-cost">50</span><p>Which caption tracks a video has,
and in which languages.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18"
height="7" rx="2"/><rect x="3" y="14" width="8" height="6" rx="2"/><rect x="13" y="14" width="8" height="6"
rx="2"/></svg></span><div><b>Channel sections</b><span class="ytca-cost">1 unit</span><p>The shelves on a
channel page.</p></div></li>
<li><span class="ytca-ico"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5"
r="6.5"/><path d="M20 20l-4.8-4.8"/></svg></span><div><b>Search</b><span
class="ytca-cost">100</span><p>Videos or channels by keyword, ready to queue.</p></div></li>
</ul>
</section>
</div>"""
HOME_URL = "/"
DOCS_URL = "/api-docs"
OPENAPI_URL = "/api-docs/openapi.json"
ASSETS_URL = "/assets"
DESIGN_SYSTEM_URL = "/design-system"
DOCS_OAUTH2_REDIRECT_URL = "/api-docs/oauth2-redirect"
CLIENT_KEY_HEADER = "X-API-Key"
MCP_URL = "/mcp"
MCP_INSTRUCTIONS = """YouTube Channel Analyzer: collects a channel's public data from the YouTube Data API
into a local database, then reads it back at no quota cost.
- Reads (list_*, get_*) are free; fetches, searches and refreshes spend YouTube quota (10,000 units a day).
- Check get_quota before large work, and use estimate_fetch_job or estimate_search for the cost first.
- Start with resolve_channel (URL, @handle or ID) to store a channel; create_fetch_job collects everything
  in the background, then poll get_fetch_job.
- delete_channel removes a channel and all its stored data; only use it when asked."""

# Paths reachable without a client key (R-15 exceptions: home, health check, API docs, design system).
PUBLIC_PATHS = frozenset(
    {HOME_URL, "/health", DOCS_URL, OPENAPI_URL, DOCS_OAUTH2_REDIRECT_URL, DESIGN_SYSTEM_URL}
)
# Static files of the public pages (stylesheets), served from public/assets.
PUBLIC_PATH_PREFIXES = (f"{ASSETS_URL}/",)


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith(PUBLIC_PATH_PREFIXES)


DEFAULT_TRANSCRIPT_LANGUAGES = ("en", "ur", "hi")
DEFAULT_TRANSCRIPT_PAUSE_SECONDS = 2.0
DEFAULT_TRANSCRIPT_MAX_ATTEMPTS = 3
DEFAULT_SHORTS_THRESHOLD_SECONDS = 180

# Swagger UI shows tag groups in this order: service checks, then search and find a channel, then the data
# from channel down to transcripts, then fetching and maintenance.
API_TAGS = [
    {
        "name": "Health",
        "description": "Checks that the API is running and can reach its Postgres database. Public, so "
        "it needs no client key; returns 200 when healthy and 503 when the database is "
        "down.",
    },
    {
        "name": "Quota",
        "description": "Shows how many of today's 10,000 YouTube Data API units are used and left, the "
        "200-unit safety margin, and when the quota resets (midnight Pacific, shown in "
        "PKT and UTC too).",
    },
    {
        "name": "Search",
        "description": "Searches YouTube for videos or channels by keyword to find competitors in a "
        "niche. Each page costs 100 units, so estimate first; any channel found can be "
        "queued for a full fetch.",
    },
    {
        "name": "Find channel",
        "description": "Turns a channel URL, @handle or channel ID into the real channel and stores its "
        "details. IDs and handles cost 1 unit; legacy /c/ URLs need a 100-unit search.",
    },
    {
        "name": "Channels",
        "description": "Reads the channels already stored in the database: name, handle, country, "
        "subscribers, views, video count, keywords and topics. Reads never spend YouTube "
        "quota.",
    },
    {
        "name": "Playlists",
        "description": "Fetches up to N of a channel's playlists from YouTube (1 unit per 50, "
        "optionally with their videos) and reads stored playlists and their videos in order. "
        "Private or deleted videos in a playlist are skipped.",
    },
    {
        "name": "Videos",
        "description": "Fetches a channel's newest N videos (about 2 units per 50) or one video by ID "
        "(1 unit) from YouTube, and reads stored videos for free: stats, tags, duration, the Shorts "
        "flag (180 seconds or less, a heuristic) and the gap since the previous upload.",
    },
    {
        "name": "Comments",
        "description": "Fetches up to N of a video's comments with their replies from YouTube (100 per "
        "unit) and reads stored comments with authors, likes and dates. Comments are also stored by "
        "fetch jobs (top 100 per video by default).",
    },
    {
        "name": "Transcripts",
        "description": "Fetches and reads video transcripts with timed segments and full text. They come"
        " from YouTube's caption data, not the Data API, so they cost no quota; manual "
        "transcripts are preferred.",
    },
    {
        "name": "Channel sections",
        "description": "The shelves on a channel's page (popular uploads, featured playlists or channels). "
        "1 unit per channel.",
    },
    {
        "name": "Captions",
        "description": "Lists which caption tracks a video has (languages, owner-made or auto-generated). "
        "50 units per video, so meant for single videos. The caption text itself comes free from the "
        "Transcripts routes.",
    },
    {
        "name": "Video categories",
        "description": "YouTube's video categories (Music, Gaming, News and so on) that give stored videos "
        "their category name. 1 unit to fetch the list.",
    },
    {
        "name": "Fetch jobs",
        "description": "The main workflow: estimate the cost, then start a background job that fetches a"
        " channel's videos, comments, playlists and transcripts. Jobs run one at a time, "
        "pause when the quota runs out and resume after the reset.",
    },
    {
        "name": "Channel refresh",
        "description": "Updates a stored channel: a stats refresh updates the channel and its video "
        "numbers, a full refresh queues a new fetch job for everything.",
    },
    {
        "name": "Channel management",
        "description": "Marks a channel tracked, or deletes a channel with all its videos, comments, "
        "playlists and transcripts.",
    },
]

# Order of operations inside each tag group ("METHOD path").
API_OPERATION_ORDER = [
    "GET /health",
    "GET /quota",
    "POST /search/estimate",
    "POST /search",
    "GET /searches",
    "GET /searches/{search_id}",
    "POST /searches/{search_id}/results/{rank}/queue",
    "POST /channels/resolve",
    "GET /channels",
    "GET /channels/{channel_id}",
    "POST /channels/{channel_id}/playlists/fetch",
    "GET /channels/{channel_id}/playlists",
    "GET /playlists/{playlist_id}/videos",
    "POST /channels/{channel_id}/videos/fetch",
    "GET /channels/{channel_id}/videos",
    "POST /videos/{video_id}/fetch",
    "GET /videos/{video_id}",
    "POST /videos/{video_id}/comments/fetch",
    "GET /videos/{video_id}/comments",
    "POST /videos/{video_id}/transcript",
    "GET /videos/{video_id}/transcript",
    "POST /channels/{channel_id}/transcripts",
    "GET /channels/{channel_id}/transcripts/status",
    "POST /channels/{channel_id}/sections/fetch",
    "GET /channels/{channel_id}/sections",
    "POST /videos/{video_id}/captions/fetch",
    "GET /videos/{video_id}/captions",
    "POST /video-categories/fetch",
    "GET /video-categories",
    "POST /fetch-jobs/estimate",
    "POST /fetch-jobs",
    "GET /fetch-jobs",
    "GET /fetch-jobs/{job_id}",
    "POST /fetch-jobs/{job_id}/cancel",
    "POST /channels/{channel_id}/refresh/stats",
    "POST /channels/{channel_id}/refresh/full",
    "PATCH /channels/{channel_id}",
    "DELETE /channels/{channel_id}",
]
