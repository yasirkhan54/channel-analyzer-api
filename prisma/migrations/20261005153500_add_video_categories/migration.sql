-- CreateTable
CREATE TABLE "video_categories" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "assignable" BOOLEAN NOT NULL,
    "channel_id" TEXT,
    "region_code" TEXT NOT NULL,
    "language" TEXT NOT NULL,
    "fetched_at" TIMESTAMPTZ(3) NOT NULL,
    "created_at" TIMESTAMPTZ(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(3) NOT NULL,

    CONSTRAINT "video_categories_pkey" PRIMARY KEY ("id")
);

