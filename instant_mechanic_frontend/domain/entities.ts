import { UrgencyLevel } from "./enums";

export interface DiagnosisResult {
  probable_causes: string[];
  urgency_level: UrgencyLevel;
  estimated_cost_range: string;
  recommended_service: string;
  mechanic_notes: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  message: string;
  state: string;
  requires_booking: boolean;
  diagnosis: DiagnosisResult | null;
}

export interface MediaUploadResponse {
  media_id: number;
  status: string;
}

export interface CreateBookingPayload {
  session_id: string;
  customer_name: string;
  phone_number: string;
  preferred_slot: string;
}

export interface BookingConfirmation {
  booking_id: string;
  status: string;
  message: string;
}

export interface BookingDetail {
  booking_id: string;
  customer_name: string;
  phone_number: string;
  preferred_slot: string;
  status: string;
  created_at: string;
}
