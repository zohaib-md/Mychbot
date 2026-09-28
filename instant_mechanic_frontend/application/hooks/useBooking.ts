"use client";

import { useCallback, useState } from "react";
import { chatApi } from "@/application/services/api";
import type { BookingConfirmation } from "@/domain/entities";

export interface BookingFormValues {
  customer_name: string;
  phone_number: string;
  preferred_slot: string;
}

export function useBooking(sessionId: string) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState<BookingConfirmation | null>(
    null,
  );
  const [bookingError, setBookingError] = useState<string | null>(null);

  const submitBooking = useCallback(
    async (values: BookingFormValues): Promise<boolean> => {
      setBookingError(null);
      setIsSubmitting(true);

      try {
        const result = await chatApi.createBooking({
          session_id: sessionId,
          customer_name: values.customer_name,
          phone_number: values.phone_number,
          preferred_slot: new Date(values.preferred_slot).toISOString(),
        });
        setConfirmation(result);
        return true;
      } catch {
        setBookingError(
          "Booking failed. Please check your details and try again.",
        );
        return false;
      } finally {
        setIsSubmitting(false);
      }
    },
    [sessionId],
  );

  return { submitBooking, isSubmitting, confirmation, bookingError };
}
