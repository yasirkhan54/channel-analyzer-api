# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Yasir Khan (owner and analyst)**: the only user in this phase. Studies a YouTube channel and its competitors: its upload pattern, which videos and formats (Shorts or long) perform, and what the audience says in comments and transcripts.
- **API clients**: scripts, notebooks or a later frontend that read the stored data through the backend API with the static client key.

## Product Purpose

A local backend that collects the full public picture of a YouTube channel (channel, every video, comments with replies, playlists, transcripts) into one Postgres store, inside YouTube's 10,000 unit daily quota, so it can be read and analysed repeatedly at zero quota cost. A keyword search finds comparable channels in the same niche, which can then be queued for a full fetch.

Success: send a channel URL, @handle or channel ID; a background job fetches everything, pauses when quota runs out and resumes after the Pacific midnight reset; the stored data is then read from our own API.

## Positioning

It does not show YouTube pages; it keeps a channel's whole public record in one place, quota-aware: fetch once (pausing and resuming around the daily quota), read forever at no quota cost.

## Operating Context

- Runs locally on the owner's computer with Docker Compose (API on http://localhost:8000, Postgres on localhost:5433). No deployment.
- Owner and operator in Pakistan: quota reset is midnight Pacific time, shown in PKT alongside Pacific.
- Our API is used through Swagger UI (`/api-docs`) or HTTP clients sending the `X-API-Key` header.
- The home page at `/` is public (no client key) and is the project's home page; `/health` and the docs are the other public paths.

## Capabilities and Constraints

- Data sources: YouTube Data API v3 (channel, videos, comments, playlists, search) with one Google API key; transcripts scraped from YouTube caption data with `youtube-transcript-api` (no quota, blocked from cloud IPs).
- Quota: 10,000 units per day; list calls cost 1 unit, search costs 100 units.
- Shorts is a heuristic (duration up to 180 seconds), always labelled as such.
- Subscriber counts are rounded by YouTube; hidden counts are empty, never 0.
- Stored data is kept until it is deleted by hand; nothing expires automatically.
- The Google API key and proxy URL are never shown, returned or logged.
- Not available or out of scope: thumbnails, growth history, private analytics (watch time, CTR, retention, revenue), dislikes, writing to YouTube, multiple users.
- Stack: FastAPI (Python 3.12, uv), PostgreSQL via Prisma Client Python, Docker Compose.

## Brand Commitments

- "YouTube Channel Analyzer" is the internal project name only. Any name shown to someone other than the owner must not start with "YouTube" (rule R-12); no public name is chosen yet.
- No YouTube logos or brand assets.
- Writing: no em dashes.

## Evidence on Hand

- Live data from the running API: `/health` (service and database status). Quota, channels and jobs need the client key.
- No users, testimonials, metrics, screenshots or benchmarks exist; none may be invented.

## Product Principles

1. Quota is the scarce resource: make cost visible before spending it, and never spend it on reads.
2. Truthful data: label heuristics, keep hidden or missing values empty, never guess.
3. Secrets stay on the server.
4. Resumable by design: long jobs pause and continue, nothing refetched twice.
