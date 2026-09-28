import { apiGet, apiPost, apiPostForm } from "@/infrastructure/http/apiClient";
import type {
  BookingConfirmation,
  BookingDetail,
  ChatResponse,
  CreateBookingPayload,
  MediaUploadResponse,
} from "@/domain/entities";

export const chatApi = {
  sendMessage: (sessionId: string, message: string) =>
    apiPost<ChatResponse>("/api/chat/", {
      session_id: sessionId,
      message,
    }),

  uploadMedia: (sessionId: string, file: File) => {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("file", file);
    return apiPostForm<MediaUploadResponse>("/api/upload/", form);
  },

  createBooking: (payload: CreateBookingPayload) =>
    apiPost<BookingConfirmation>("/api/booking/", payload),

  getBooking: (bookingId: string) =>
    apiGet<BookingDetail>(`/api/booking/${bookingId}/`),
};
