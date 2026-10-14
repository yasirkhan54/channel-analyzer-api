-- CreateTable
CREATE TABLE "video_caption_tracks" (
    "id" TEXT NOT NULL,
    "video_id" TEXT NOT NULL,
    "language" TEXT NOT NULL,
    "name" TEXT,
    "track_kind" TEXT NOT NULL,
    "audio_track_type" TEXT,
    "is_cc" BOOLEAN,
    "is_large" BOOLEAN,
    "is_easy_reader" BOOLEAN,
    "is_draft" BOOLEAN,
    "is_auto_synced" BOOLEAN,
    "status" TEXT,
    "failure_reason" TEXT,
    "last_updated" TIMESTAMPTZ(3),
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "video_caption_tracks_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "video_caption_tracks_video_id_idx" ON "video_caption_tracks"("video_id");

-- AddForeignKey
ALTER TABLE "video_caption_tracks" ADD CONSTRAINT "video_caption_tracks_video_id_fkey" FOREIGN KEY ("video_id") REFERENCES "videos"("id") ON DELETE CASCADE ON UPDATE CASCADE;

