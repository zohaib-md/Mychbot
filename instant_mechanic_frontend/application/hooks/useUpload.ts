"use client";

import { useCallback, useState } from "react";
import { chatApi } from "@/application/services/api";

const ALLOWED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "audio/mpeg",
  "audio/wav",
  "video/mp4",
]);
const MAX_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

export function useUpload(sessionId: string) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [lastUploadedId, setLastUploadedId] = useState<number | null>(null);

  const uploadFile = useCallback(
    async (file: File): Promise<boolean> => {
      setUploadError(null);

      // Client-side validation before hitting the server
      if (!ALLOWED_TYPES.has(file.type)) {
        setUploadError(
          `File type "${file.type}" is not supported. Please upload an image, audio, or video file.`,
        );
        return false;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setUploadError(
          `File is too large (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum size is 20 MB.`,
        );
        return false;
      }

      setIsUploading(true);
      try {
        const result = await chatApi.uploadMedia(sessionId, file);
        setLastUploadedId(result.media_id);
        return true;
      } catch {
        setUploadError("Upload failed. Please try again.");
        return false;
      } finally {
        setIsUploading(false);
      }
    },
    [sessionId],
  );

  return { uploadFile, isUploading, uploadError, lastUploadedId };
}
