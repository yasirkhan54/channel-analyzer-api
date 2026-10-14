"""Long Swagger descriptions for every route, written as Markdown (Swagger UI renders it).

Kept flush left on purpose: indented lines would render as code blocks.
"""

# Health

HEALTH = """
Checks that the API is running and can reach Postgres. Needs no API key and spends no quota.

- **200** `{"status": "ok", "database": "ok"}`
- **503** `{"status": "error", "database": "error"}` when the database cannot be reached.
"""

QUOTA = """
Shows today's YouTube Data API usage as counted by this service's own ledger. Spends no quota.

- The quota day is the **Pacific day**: it resets at midnight Pacific time (12:00 PKT, 13:00 PKT in winter).
- `units_used` counts only calls made by this service. Calls made elsewhere with the same Google key are not
  included.
- `units_remaining` is `daily_limit - units_used`. Calls that cost quota stop earlier, when they would
  reach the `safety_margin`.
- `used`, `remaining` and `margin` are short aliases of the three main fields.
"""

# Find channel

RESOLVE_CHANNEL = """
Finds a YouTube channel and stores its details (title, handle, country, creation date, subscribers, views,
video count, keywords, topics). **It stores no videos, comments or playlists.** Use the fetch routes or a
fetch job for those.

**Accepted `input`**
- Channel ID: `UCxxxxxxxxxxxxxxxxxxxxxx`
- Handle: `@name` or `youtube.com/@name`
- Channel URL: `youtube.com/channel/UC...`
- Old username URL: `youtube.com/user/name`
- Legacy custom URL: `youtube.com/c/name` (expensive, see below)

**Quota**
| Input | Cost |
|---|---|
| Channel ID, already stored and fetched in the last 30 days | **0** (`cached: true`) |
| Channel ID, not stored or older than 30 days | 1 |
| @handle | 1 (2 if it falls back to a username lookup) |
| /user/ URL | 1 |
| /c/ URL | **101** (a 100-unit search plus 1) and only with `confirm_legacy: true` |

`refresh: true` skips the stored copy and always calls YouTube. Only a channel ID input is served from the
stored copy, so a handle always costs at least 1 unit.

**Errors**
- **400**: empty or invalid input, or a /c/ URL without `confirm_legacy: true`.
- **404**: no channel found on YouTube.
- **429**: today's quota (minus the safety margin) is used up.
- **502**: YouTube returned an error.
"""

# Channels and videos (stored data)

LIST_CHANNELS = """
Lists the channels stored in the database, sorted by title. Spends no quota.

Paged with `page` (from 1) and `page_size` (1 to 100, default 50). `total` is the number of stored channels.
"""

GET_CHANNEL = """
Returns one stored channel. Spends no quota.

**404** when the channel is not in the database. Store it first with `POST /channels/resolve` or a fetch job.
"""

LIST_CHANNEL_VIDEOS = """
Lists a stored channel's stored videos. Spends no quota. Shows only videos already fetched; it does not call
YouTube.

**Filters**
- `is_short`: `true` for Shorts only, `false` for long videos only. Shorts are detected by duration (up to 180
  seconds), so this is a heuristic.
- `is_live`: `true` for live streams and premieres (scheduled or started), `false` for normal uploads.
- `published_after` / `published_before`: date range, inclusive.

**Sorting**
- `sort_by`: `published_at` (default), `view_count`, `like_count`, `comment_count`, `duration_seconds`.
- `order`: `desc` (default) or `asc`.
- Videos with no value for the sort field (hidden likes, disabled comments) always come last.

Paged with `page` and `page_size` (1 to 100, default 50). **404** when the channel is not stored.
"""

GET_VIDEO = """
Returns one stored video with its stats, duration, category, language, captions flag, live details,
Shorts flag, upload gap and transcript status. Spends no quota.

**404** when the video is not stored. Use `POST /videos/{video_id}/fetch` to store it.
"""

# Videos (fetch from YouTube)

FETCH_CHANNEL_VIDEOS = """
Fetches a channel's **newest `max_videos` uploads** from YouTube with full details and stores them.
Runs inside the request: the response comes when the work is done.

**What it does**
1. Uses the stored channel, or fetches and stores it first when it is missing or older than 30 days (1 unit).
2. Lists the newest uploads from the channel's uploads playlist (1 unit per 50).
3. Fetches full details for those videos (1 unit per 50) and stores them. Existing videos are updated, never
   duplicated.
4. With `comments_per_video` above 0, fetches that many top comments of each video (relevance order) with
   all their replies.

**Body**
- `max_videos`: 1 to 500, default 50.
- `comments_per_video`: 0 to 100, default 0 (no comments).

**Quota**: about 2 units per 50 videos, plus about 1 unit per video when comments are on (more for videos
whose comments have many replies).

For a whole channel, use `POST /fetch-jobs` instead: it runs in the background, pauses when the quota runs
out and resumes later.

**Errors**: **404** channel not found on YouTube, **429** quota used up, **502** YouTube error.
"""

FETCH_VIDEO = """
Fetches one video's full details from YouTube and stores it, updating it if it is already stored.

- If the video's channel is not stored (or is older than 30 days), the channel is fetched and stored too.
- The channel's upload gaps (time since the previous upload) are recalculated.

**Quota**: 1 unit, plus 1 when the channel had to be fetched.

**Errors**: **404** the video does not exist or is not public, **429** quota used up, **502** YouTube error.
"""

# Comments

FETCH_VIDEO_COMMENTS = """
Fetches a video's comments from YouTube and stores them. Existing comments are updated, never duplicated.
If the video is not stored yet, the video (and its channel when needed) is fetched first.

**Body**
- `max_comments`: top-level comments to fetch, 1 to 1000, default 100.
- `order`: `relevance` (top comments, default) or `time` (newest first).
- `include_replies`: default `true`. Stores every reply of each fetched comment.

**Quota**
- 1 unit per 100 top-level comments.
- YouTube sends the first few replies of each comment for free. A comment with more replies costs 1 more
  unit per 100 replies.
- Plus 1 or 2 units when the video or its channel had to be fetched first.

When the video has comments turned off, the call succeeds with `comments_disabled: true` and nothing stored.

**Errors**: **404** video not found on YouTube, **429** quota used up, **502** YouTube error.
"""

LIST_VIDEO_COMMENTS = """
Lists a stored video's stored comments. Spends no quota.

Each item is a **top-level comment** with all its stored `replies` (oldest reply first). Paging and the
`total` count apply to top-level comments only.

- `sort_by`: `like_count` (default) or `published_at`.
- `order`: `desc` (default) or `asc`.

**404** when the video is not stored.
"""

# Playlists

FETCH_CHANNEL_PLAYLISTS = """
Fetches a channel's playlists from YouTube and stores them. Runs inside the request. Existing playlists are
updated, never duplicated.

**What it does**
1. Uses the stored channel, or fetches and stores it first when it is missing or older than 30 days (1 unit).
2. Fetches up to `max_playlists` playlists (title, description, date, video count).
3. With `include_videos: true`, also stores each playlist's video list in playlist order, and the full
   details of those videos.

**Body**
- `max_playlists`: 1 to 500, default 10.
- `include_videos`: default `false`.

**Quota**
- 1 unit per 50 playlists.
- With `include_videos`: about 2 units per 50 playlist videos.

Videos in a playlist that belong to a channel that is not stored are linked to the playlist, but their
details are skipped. `videos_from_other_channels` counts them.

**Errors**: **404** channel not found on YouTube, **429** quota used up, **502** YouTube error.
"""

LIST_CHANNEL_PLAYLISTS = """
Lists a stored channel's stored playlists, sorted by title. Spends no quota.

Paged with `page` and `page_size`. **404** when the channel is not stored.
"""

LIST_PLAYLIST_VIDEOS = """
Lists a stored playlist's videos in playlist order. Spends no quota.

- `video` holds the full stored video when it is in the database, and is empty when it is not (for example
  a video from another channel).
- `video_available: false` marks a private or deleted video.

Paged with `page` and `page_size`. **404** when the playlist is not stored.
"""

# Transcripts

FETCH_VIDEO_TRANSCRIPT = """
Fetches the transcript (captions) of one **stored** video and stores it with timed segments and full text.

- **Costs no YouTube Data API quota.** It reads YouTube's caption data directly, not through the Data API.
- Picks a manually made transcript before an auto-generated one, trying `preferred_languages` in order
  (default `en`, `ur`, `hi`) and the video's own language.
- Temporary errors are retried up to 3 times.
- A new fetch replaces the stored transcript and its segments.

The response is the stored transcript. Its `status` is `available`, or `none` (no captions), `disabled`
(captions turned off) or `failed`.

**Errors**
- **404**: the video is not stored. Fetch it first with `POST /videos/{video_id}/fetch`.
- **503**: YouTube is blocking transcript requests from this machine. Try again later.
"""

GET_VIDEO_TRANSCRIPT = """
Returns a video's stored transcript. Spends no quota and does not call YouTube.

- `format=segments` (default): full text plus every segment with `start_seconds` and `duration_seconds`.
- `format=text`: full text only, without segments.

**404** when the video is not stored or has no stored transcript.
"""

FETCH_CHANNEL_TRANSCRIPTS = """
Fetches transcripts for a channel's videos **that are already stored** and stores them. It does not look
for new videos, so fetch the videos first.

- **Costs no YouTube Data API quota.**
- Goes through the videos newest first, one at a time, with a **2-second pause** between videos so YouTube
  does not block it.
- `only_missing: true` (default) skips videos whose transcript is already `available`. `false` fetches
  every video again.
- `preferred_languages`: language order, default `en`, `ur`, `hi`.
- If YouTube starts blocking requests it **stops at once** and leaves the remaining videos for later.

**Runs inside the request**, so a channel with many videos takes long (about 2 seconds per video; 500 videos
take over 15 minutes) and the client may time out. The work still finishes on the server. For large channels
use a fetch job with `transcripts_requested: true`.

**Response**: counts per result (`available`, `none`, `disabled`, `failed`, `blocked`) and `step_status`:
`done` (all handled), `partial` (stopped early) or `blocked` (YouTube blocked it).

**404** when the channel is not stored.
"""

LIST_CHANNEL_TRANSCRIPT_STATUS = """
Lists a stored channel's stored videos, newest first, with the transcript status of each. Spends no quota.

- `status` filter: `pending`, `available`, `none`, `disabled`, `blocked` or `failed`. Useful to find the
  videos still missing a transcript.
- Each item shows the language, whether it was auto-generated, the number of attempts and the last error.

Paged with `page` and `page_size`. **404** when the channel is not stored.
"""

# Search

ESTIMATE_SEARCH = """
Shows what a search would cost before running it. **Spends no quota.** Takes the same body as `POST /search`.

- `quota_cost`: `pages × 100` units (each search page costs 100 units).
- `units_available`: units left today above the safety margin.
- `allowed`: whether the search fits.
"""

RUN_SEARCH = """
Searches YouTube by keyword for **videos** or **channels**, and stores the search and its results.

**Body**
- `keyword` (required) and `type`: `video` (default) or `channel`.
- Optional filters: `region_code` (two letters, e.g. `PK`), `relevance_language` (e.g. `ur`),
  `published_after`, `published_before`.
- `order`: `relevance` (default), `date`, `rating`, `title`, `viewCount`, `videoCount`.
- `pages`: 1 to 5, default 1. `results_per_page`: 1 to 50, default 50.

**Quota: 100 units per page.** The search is refused up front when the units available today are not enough.
If the quota runs out after the first page, the pages already paid for are kept. It stops early when YouTube
has no more pages.

Results are stored with their rank and title. A video result also carries its channel ID, so any result can
be queued for a full channel fetch with `POST /searches/{search_id}/results/{rank}/queue`. The videos and
channels found are **not** fetched or stored by the search itself.

**Errors**: **429** not enough quota (the message gives the reset time in PKT), **502** YouTube error.
"""

LIST_SEARCHES = """
Lists stored searches, newest first, without their results. Spends no quota.

Paged with `page` and `page_size`.
"""

GET_SEARCH = """
Returns one stored search with all its results in rank order. Spends no quota.

**404** when the search is not stored.
"""

QUEUE_SEARCH_RESULT = """
Starts a **full background fetch** (a fetch job) for the channel of one search result. For a video result,
that is the channel that uploaded the video.

**Body** (optional)
- `comment_mode`: `top_100` (default), `all` or `skip`.
- `transcripts_requested`: `true` or `false`. Left empty, transcripts are on for channels with fewer than
  200 videos.

Returns the new job at once. Follow it with `GET /fetch-jobs/{job_id}`.

**Errors**: **404** no result with that rank in that search, **422** the result has no channel.
"""

# Fetch jobs

CREATE_FETCH_JOB = """
Starts a **background fetch of a whole channel** and returns the job at once (`status: queued`). The work
runs in the background, so nothing waits on this request.

**What the job does, in order**
1. `channel`: finds the channel and stores its details.
2. `videos`: stores every upload with full details.
3. `comments`: stores comments as set by `comment_mode`.
4. `playlists`: stores every playlist with its videos in order.
5. `transcripts`: stores transcripts, if requested.

**Body**
- `channel_input` (required): channel URL, @handle or channel ID.
- `comment_mode`: `top_100` (default, top 100 comments of each video with all replies), `all` (every
  comment and reply; can be expensive) or `skip`.
- `transcripts_requested`: `true` or `false`. Left empty, transcripts are on for channels with fewer than
  200 videos and off for larger ones.
- `type`: `full_fetch` (default). `full_refresh` and `stats_refresh` are normally created through the
  `/channels/{channel_id}/refresh/...` routes.

**How jobs run**
- One job at a time, in the order they were created.
- Progress is saved after every page. When the quota runs out the job becomes `paused_for_quota` and later
  continues from where it stopped instead of starting over.
- See the cost first with `POST /fetch-jobs/estimate`.
"""

LIST_FETCH_JOBS = """
Lists fetch jobs, newest first. Spends no quota.

- `status` filter: `queued`, `running`, `paused_for_quota`, `completed`, `failed` or `cancelled`.

Paged with `page` and `page_size`.
"""

ESTIMATE_FETCH_JOB = """
Estimates what a fetch job would cost before starting it. **Spends no quota and calls no YouTube API.**

- Uses the stored channel's video count when the channel is already stored (looked up by channel ID or
  handle). Otherwise it **assumes 100 videos**, so the estimate is rough for a channel not yet stored.
  Resolve the channel first (`POST /channels/resolve`, 1 unit) for a real figure.
- `estimated_quota_units_min` / `_max`: a range, because the number of comments and replies per video is
  only known after fetching. The range is widest for `comment_mode: all`.
- `estimated_transcript_time_*`: about 2 seconds per video when transcripts are on.
- `quota_available`: whether today's remaining units (above the safety margin) cover the minimum estimate.
- `warning`: set for legacy /c/ URLs, which cost 100 extra units to resolve.
"""

GET_FETCH_JOB = """
Returns a fetch job's status and progress. Spends no quota. Poll this to follow a running job.

- `status`: `queued` → `running` → `completed`, or `paused_for_quota`, `failed` (see `error_detail`) or
  `cancelled`.
- `stage`: the step it is on: `channel`, `videos`, `comments`, `playlists` or `transcripts`.
- Progress counters: `videos_found` (the channel's video count), `videos_done`, `comments_fetched`,
  `playlists_done`, `transcripts_done`, `transcripts_missing`, `transcripts_blocked`.
- `transcript_step_status`: `not_requested`, `pending`, `running`, `done`, `partial` or `blocked`.
- `quota_spent`: units this job has used so far.
- `resume_cursor`: where the job will continue after a pause (internal bookkeeping).

**404** when the job does not exist.
"""

CANCEL_FETCH_JOB = """
Cancels a `queued`, `running` or `paused_for_quota` job. A running job stops at its next checkpoint (between
pages or videos). **Data already fetched stays stored.**

**Errors**: **404** job not found, **400** the job is already `completed`, `failed` or `cancelled`.
"""

# Channel refresh

REFRESH_STATS = """
Updates the numbers of a **stored** channel and its **stored** videos. Runs inside the request.

- Fetches the channel again (subscribers, total views, video count and other details).
- Updates **views, likes and comment count** of every stored video, 50 videos per call.
- **Does not** look for new videos, and does not touch comments, playlists or transcripts.

**Quota**: 1 unit for the channel plus 1 unit per 50 stored videos. Cheap.

Use it to see how the numbers have changed. Use `/refresh/full` to also pick up new videos.

**Errors**: **404** channel not stored, **429** quota used up, **502** YouTube error.
"""

REFRESH_FULL = """
Queues a **full refresh** of a **stored** channel as a background fetch job and returns the job at once.
Follow it with `GET /fetch-jobs/{job_id}`.

The job fetches everything again: the channel, every video (**including new uploads**), comments as set by
`comment_mode`, playlists and, if requested, transcripts. Records are updated in place, never duplicated.

**Body** (optional)
- `comment_mode`: `top_100` (default), `all` or `skip`.
- `transcripts_requested`: `true` to include transcripts. Left empty, transcripts are **off** for a refresh.

**Quota**: about the same as a first full fetch. See `POST /fetch-jobs/estimate`.

**404** when the channel is not stored.
"""

# Channel management

DELETE_CHANNEL = """
**Permanently deletes** a stored channel with all of its data: videos, comments, playlists, playlist entries,
transcripts, and search results that point at the channel or its videos. Cannot be undone.

- Fetch jobs of the channel are kept for history, with their channel link cleared.
- Spends no quota.

**Responses**: **204** deleted, **404** channel not stored, **409** the channel has a queued, running or
paused fetch job (cancel it first).
"""

UPDATE_CHANNEL_TRACKING = """
Marks a stored channel as tracked (`tracked: true`) or not tracked. Spends no quota.

The flag marks the channels you follow. **Only the flag is stored for now: nothing refreshes tracked
channels automatically.** Refresh them yourself with `POST /channels/{channel_id}/refresh/stats` or
`POST /channels/{channel_id}/refresh/full`.

**404** when the channel is not stored.
"""

# Captions

FETCH_VIDEO_CAPTIONS = """
Lists a video's **caption tracks** from YouTube (`captions.list`) and stores them. It tells you which
languages have captions and how each was made. **It does not return the caption text**: for the text use the
free transcript routes (`POST /videos/{video_id}/transcript`).

- **Costs 50 units per video.** That is expensive: Mubasher Lucman's 6,525 videos would cost about 326,250
  units, more than 32 days of quota. Use it for single videos, not whole channels.
- If the video is not stored yet, the video (and its channel when needed) is fetched first, 1 or 2 more units.
- Each fetch replaces the stored list, so tracks the owner removed disappear.

**Each track**
- `language`: language code, e.g. `en`, `ur`.
- `track_kind`: `standard` (uploaded by the owner), `asr` (auto-generated by YouTube) or `forced`.
- `name`, `is_cc` (closed captions), `is_draft`, `is_auto_synced`, `status` (`serving`, `syncing`,
  `failed`) and `last_updated`.

Only listing works with this service's API key. Downloading, uploading, editing and deleting caption tracks
need the video owner's sign-in (OAuth), so they are not offered.

**Errors**: **404** the video does not exist or is not public, **429** quota used up, **502** YouTube error.
"""

LIST_VIDEO_CAPTIONS = """
Returns a video's stored caption tracks, sorted by language. Spends no quota and does not call YouTube.

The list is empty until `POST /videos/{video_id}/captions/fetch` has run for the video.

**404** when the video is not stored.
"""

# Video categories

FETCH_VIDEO_CATEGORIES = """
Fetches YouTube's list of **video categories** (Music, Gaming, News & Politics and so on) and stores them.
**Costs 1 unit.**

**Body** (optional)
- `region_code`: two letters, default `US`. Regions can differ in which categories uploaders may pick.
- `language`: language of the titles, default `en` (for example `ur` for Urdu titles).

Stored videos keep a `category_id`, and their `category_name` comes from this list. The video fetch routes
already fill it in on their own (and store the list the first time). Use this route to refresh the list or
load it in another language.

Category IDs are the same in every region, so a new fetch updates the stored titles.

**Errors**: **429** quota used up, **502** YouTube error (for example an unknown region code).
"""

LIST_VIDEO_CATEGORIES = """
Returns the stored video categories, sorted by ID. Spends no quota and does not call YouTube.

- `assignable`: whether uploaders can choose the category for a new video.
- Empty until `POST /video-categories/fetch` has run, or until a video fetch has stored the list.
"""

# Channel sections

FETCH_CHANNEL_SECTIONS = """
Fetches a channel's **sections** (the shelves on its channel page, such as Popular uploads, a featured
playlist or featured channels) from YouTube and stores them. **Costs 1 unit.**

- If the channel is not stored, or is older than 30 days, it is fetched first (1 more unit).
- Each fetch replaces the stored list, so sections the owner removed disappear.
- Many channels have none, or only the default ones.

**Each section**
- `type`: what it shows, as YouTube sends it (lowercase), for example `recentuploads`, `popularuploads`,
  `singleplaylist`, `multipleplaylists`, `multiplechannels` or `subscriptions`.
  `channelsectiontypeundefined` marks a newer kind of shelf the API does not describe.
- `position`: order on the channel page, from 0.
- `title`: only for sections with a custom title.
- `playlist_ids` / `channel_ids`: the playlists or channels the section features. Fetch those with the
  playlist routes or `POST /channels/resolve`. YouTube sometimes leaves `channel_ids` empty even for a
  featured-channels section.

Only listing works with this service's API key. Adding, editing and deleting sections need the channel
owner's sign-in (OAuth), so they are not offered.

**Errors**: **404** channel not found on YouTube, **429** quota used up, **502** YouTube error.
"""

LIST_CHANNEL_SECTIONS = """
Returns a stored channel's stored sections in page order. Spends no quota and does not call YouTube.

The list is empty until `POST /channels/{channel_id}/sections/fetch` has run for the channel.

**404** when the channel is not stored.
"""
