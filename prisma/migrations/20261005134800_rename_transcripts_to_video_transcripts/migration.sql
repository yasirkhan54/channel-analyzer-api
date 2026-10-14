-- Rename tables
ALTER TABLE "transcripts" RENAME TO "video_transcripts";
ALTER TABLE "transcript_segments" RENAME TO "video_transcript_segments";

-- Rename sequences
ALTER SEQUENCE "transcripts_id_seq" RENAME TO "video_transcripts_id_seq";
ALTER SEQUENCE "transcript_segments_id_seq" RENAME TO "video_transcript_segments_id_seq";

-- Rename primary keys
ALTER TABLE "video_transcripts" RENAME CONSTRAINT "transcripts_pkey" TO "video_transcripts_pkey";
ALTER TABLE "video_transcript_segments" RENAME CONSTRAINT "transcript_segments_pkey" TO "video_transcript_segments_pkey";

-- Rename foreign keys
ALTER TABLE "video_transcripts" RENAME CONSTRAINT "transcripts_video_id_fkey" TO "video_transcripts_video_id_fkey";
ALTER TABLE "video_transcript_segments" RENAME CONSTRAINT "transcript_segments_transcript_id_fkey" TO "video_transcript_segments_transcript_id_fkey";

-- Rename indexes
ALTER INDEX "transcripts_video_id_key" RENAME TO "video_transcripts_video_id_key";
ALTER INDEX "transcript_segments_transcript_id_position_key" RENAME TO "video_transcript_segments_transcript_id_position_key";
