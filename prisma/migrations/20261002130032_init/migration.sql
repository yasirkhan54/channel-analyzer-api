-- CreateEnum
CREATE TYPE "transcript_status" AS ENUM ('pending', 'available', 'none', 'disabled', 'blocked', 'failed');

-- CreateEnum
CREATE TYPE "fetch_job_type" AS ENUM ('full_fetch', 'stats_refresh', 'full_refresh');

-- CreateEnum
CREATE TYPE "comment_mode" AS ENUM ('top_100', 'all', 'skip');

-- CreateEnum
CREATE TYPE "fetch_job_status" AS ENUM ('queued', 'running', 'paused_for_quota', 'completed', 'failed', 'cancelled');

-- CreateEnum
CREATE TYPE "fetch_job_stage" AS ENUM ('channel', 'videos', 'comments', 'playlists', 'transcripts');

-- CreateEnum
CREATE TYPE "transcript_step_status" AS ENUM ('not_requested', 'pending', 'running', 'done', 'partial', 'blocked');

-- CreateEnum
CREATE TYPE "search_type" AS ENUM ('video', 'channel');

-- CreateTable
CREATE TABLE "channels" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "custom_url" TEXT,
    "country" TEXT,
    "published_at" TIMESTAMPTZ(3),
    "subscriber_count" BIGINT,
    "subscriber_count_hidden" BOOLEAN NOT NULL DEFAULT false,
    "view_count" BIGINT,
    "video_count" INTEGER,
    "keywords" TEXT[],
    "topic_categories" TEXT[],
    "uploads_playlist_id" TEXT,
    "tracked" BOOLEAN NOT NULL DEFAULT false,
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "channels_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "videos" (
    "id" TEXT NOT NULL,
    "channel_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "tags" TEXT[],
    "published_at" TIMESTAMPTZ(3) NOT NULL,
    "duration_iso" TEXT,
    "duration_seconds" INTEGER,
    "is_short" BOOLEAN NOT NULL DEFAULT false,
    "upload_gap_seconds" BIGINT,
    "view_count" BIGINT,
    "like_count" BIGINT,
    "comment_count" BIGINT,
    "category_id" TEXT,
    "category_name" TEXT,
    "default_language" TEXT,
    "default_audio_language" TEXT,
    "definition" TEXT,
    "captions_available" BOOLEAN,
    "made_for_kids" BOOLEAN,
    "live_scheduled_start_at" TIMESTAMPTZ(3),
    "live_actual_start_at" TIMESTAMPTZ(3),
    "live_actual_end_at" TIMESTAMPTZ(3),
    "transcript_status" "transcript_status" NOT NULL DEFAULT 'pending',
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "videos_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "comments" (
    "id" TEXT NOT NULL,
    "video_id" TEXT NOT NULL,
    "parent_id" TEXT,
    "text" TEXT NOT NULL,
    "author_display_name" TEXT,
    "author_channel_id" TEXT,
    "like_count" INTEGER NOT NULL DEFAULT 0,
    "total_reply_count" INTEGER,
    "published_at" TIMESTAMPTZ(3) NOT NULL,
    "edited_at" TIMESTAMPTZ(3),
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "comments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "playlists" (
    "id" TEXT NOT NULL,
    "channel_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "published_at" TIMESTAMPTZ(3),
    "item_count" INTEGER,
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "playlists_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "playlist_items" (
    "id" TEXT NOT NULL,
    "playlist_id" TEXT NOT NULL,
    "video_id" TEXT NOT NULL,
    "position" INTEGER NOT NULL,
    "video_available" BOOLEAN NOT NULL DEFAULT true,
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "playlist_items_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "transcripts" (
    "id" SERIAL NOT NULL,
    "video_id" TEXT NOT NULL,
    "status" "transcript_status" NOT NULL DEFAULT 'pending',
    "language_code" TEXT,
    "language_name" TEXT,
    "is_generated" BOOLEAN,
    "full_text" TEXT,
    "segment_count" INTEGER NOT NULL DEFAULT 0,
    "attempt_count" INTEGER NOT NULL DEFAULT 0,
    "last_error" TEXT,
    "fetched_at" TIMESTAMPTZ(3),
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "transcripts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "transcript_segments" (
    "id" BIGSERIAL NOT NULL,
    "transcript_id" INTEGER NOT NULL,
    "position" INTEGER NOT NULL,
    "start_seconds" DOUBLE PRECISION NOT NULL,
    "duration_seconds" DOUBLE PRECISION NOT NULL,
    "text" TEXT NOT NULL,

    CONSTRAINT "transcript_segments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "fetch_jobs" (
    "id" SERIAL NOT NULL,
    "channel_input" TEXT NOT NULL,
    "channel_id" TEXT,
    "type" "fetch_job_type" NOT NULL DEFAULT 'full_fetch',
    "comment_mode" "comment_mode" NOT NULL DEFAULT 'top_100',
    "status" "fetch_job_status" NOT NULL DEFAULT 'queued',
    "stage" "fetch_job_stage",
    "transcripts_requested" BOOLEAN NOT NULL DEFAULT false,
    "transcript_step_status" "transcript_step_status" NOT NULL DEFAULT 'not_requested',
    "videos_found" INTEGER NOT NULL DEFAULT 0,
    "videos_done" INTEGER NOT NULL DEFAULT 0,
    "comments_fetched" INTEGER NOT NULL DEFAULT 0,
    "playlists_done" INTEGER NOT NULL DEFAULT 0,
    "transcripts_done" INTEGER NOT NULL DEFAULT 0,
    "transcripts_missing" INTEGER NOT NULL DEFAULT 0,
    "transcripts_blocked" INTEGER NOT NULL DEFAULT 0,
    "resume_cursor" JSONB,
    "quota_spent" INTEGER NOT NULL DEFAULT 0,
    "error_detail" TEXT,
    "started_at" TIMESTAMPTZ(3),
    "finished_at" TIMESTAMPTZ(3),
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "fetch_jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "quota_usage" (
    "quota_day" DATE NOT NULL,
    "google_project_id" TEXT NOT NULL DEFAULT 'default',
    "units_spent" INTEGER NOT NULL DEFAULT 0,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "quota_usage_pkey" PRIMARY KEY ("quota_day","google_project_id")
);

-- CreateTable
CREATE TABLE "search_queries" (
    "id" SERIAL NOT NULL,
    "keyword" TEXT NOT NULL,
    "type" "search_type" NOT NULL,
    "filters" JSONB,
    "quota_spent" INTEGER NOT NULL DEFAULT 0,
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "search_queries_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "search_results" (
    "id" SERIAL NOT NULL,
    "search_query_id" INTEGER NOT NULL,
    "rank" INTEGER NOT NULL,
    "result_type" "search_type" NOT NULL,
    "video_id" TEXT,
    "channel_id" TEXT,
    "title" TEXT,

    CONSTRAINT "search_results_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "channels_fetched_at_idx" ON "channels"("fetched_at");

-- CreateIndex
CREATE INDEX "videos_channel_id_published_at_idx" ON "videos"("channel_id", "published_at");

-- CreateIndex
CREATE INDEX "videos_fetched_at_idx" ON "videos"("fetched_at");

-- CreateIndex
CREATE INDEX "comments_video_id_idx" ON "comments"("video_id");

-- CreateIndex
CREATE INDEX "comments_parent_id_idx" ON "comments"("parent_id");

-- CreateIndex
CREATE INDEX "playlists_channel_id_idx" ON "playlists"("channel_id");

-- CreateIndex
CREATE INDEX "playlist_items_playlist_id_position_idx" ON "playlist_items"("playlist_id", "position");

-- CreateIndex
CREATE INDEX "playlist_items_video_id_idx" ON "playlist_items"("video_id");

-- CreateIndex
CREATE UNIQUE INDEX "transcripts_video_id_key" ON "transcripts"("video_id");

-- CreateIndex
CREATE UNIQUE INDEX "transcript_segments_transcript_id_position_key" ON "transcript_segments"("transcript_id", "position");

-- CreateIndex
CREATE INDEX "fetch_jobs_status_created_at_idx" ON "fetch_jobs"("status", "created_at");

-- CreateIndex
CREATE INDEX "fetch_jobs_channel_id_idx" ON "fetch_jobs"("channel_id");

-- CreateIndex
CREATE INDEX "search_queries_fetched_at_idx" ON "search_queries"("fetched_at");

-- CreateIndex
CREATE UNIQUE INDEX "search_results_search_query_id_rank_key" ON "search_results"("search_query_id", "rank");

-- AddForeignKey
ALTER TABLE "videos" ADD CONSTRAINT "videos_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "channels"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "comments" ADD CONSTRAINT "comments_video_id_fkey" FOREIGN KEY ("video_id") REFERENCES "videos"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "comments" ADD CONSTRAINT "comments_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "comments"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "playlists" ADD CONSTRAINT "playlists_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "channels"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "playlist_items" ADD CONSTRAINT "playlist_items_playlist_id_fkey" FOREIGN KEY ("playlist_id") REFERENCES "playlists"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "transcripts" ADD CONSTRAINT "transcripts_video_id_fkey" FOREIGN KEY ("video_id") REFERENCES "videos"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "transcript_segments" ADD CONSTRAINT "transcript_segments_transcript_id_fkey" FOREIGN KEY ("transcript_id") REFERENCES "transcripts"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "fetch_jobs" ADD CONSTRAINT "fetch_jobs_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "channels"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "search_results" ADD CONSTRAINT "search_results_search_query_id_fkey" FOREIGN KEY ("search_query_id") REFERENCES "search_queries"("id") ON DELETE CASCADE ON UPDATE CASCADE;
