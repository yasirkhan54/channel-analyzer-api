-- Rename table
ALTER TABLE "comments" RENAME TO "video_comments";

-- Rename primary key
ALTER TABLE "video_comments" RENAME CONSTRAINT "comments_pkey" TO "video_comments_pkey";

-- Rename foreign keys
ALTER TABLE "video_comments" RENAME CONSTRAINT "comments_video_id_fkey" TO "video_comments_video_id_fkey";
ALTER TABLE "video_comments" RENAME CONSTRAINT "comments_parent_id_fkey" TO "video_comments_parent_id_fkey";

-- Rename indexes
ALTER INDEX "comments_video_id_idx" RENAME TO "video_comments_video_id_idx";
ALTER INDEX "comments_parent_id_idx" RENAME TO "video_comments_parent_id_idx";
