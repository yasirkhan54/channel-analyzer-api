-- CreateTable
CREATE TABLE "channel_sections" (
    "id" TEXT NOT NULL,
    "channel_id" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "title" TEXT,
    "position" INTEGER NOT NULL,
    "playlist_ids" TEXT[],
    "channel_ids" TEXT[],
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "channel_sections_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "channel_sections_channel_id_idx" ON "channel_sections"("channel_id");

-- AddForeignKey
ALTER TABLE "channel_sections" ADD CONSTRAINT "channel_sections_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "channels"("id") ON DELETE CASCADE ON UPDATE CASCADE;

