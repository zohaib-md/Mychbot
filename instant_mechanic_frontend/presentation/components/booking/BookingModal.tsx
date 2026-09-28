"use client";

import { useEffect, useRef, useState } from "react";
import { useBooking } from "@/application/hooks/useBooking";

interface BookingModalProps {
  sessionId: string;
  onClose: () => void;
  onConfirmed?: () => void;
}

export default function BookingModal({
  sessionId,
  onClose,
  onConfirmed,
}: BookingModalProps) {
  const { submitBooking, isSubmitting, confirmation, bookingError } =
    useBooking(sessionId);

  const [form, setForm] = useState({
    customer_name: "",
    phone_number: "",
    preferred_slot: "",
  });

  // Focus trap: focus first input on open
  const firstInputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    firstInputRef.current?.focus();
  }, []);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await submitBooking(form);
    if (ok) onConfirmed?.();
  };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 px-4 pb-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="booking-modal-title"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800">
        {confirmation ? (
          /* Success state */
          <div className="text-center">
            <div className="mb-3 text-4xl" aria-hidden="true">✅</div>
            <h2 className="mb-2 text-lg font-bold text-gray-900 dark:text-gray-100">
              Booking Confirmed!
            </h2>
            <p className="mb-1 text-sm text-gray-600 dark:text-gray-400">
              {confirmation.message}
            </p>
            <p className="mb-4 rounded-lg bg-gray-100 px-4 py-2 font-mono text-xs text-gray-700 dark:bg-gray-700 dark:text-gray-300">
              Ref: {confirmation.booking_id}
            </p>
            <button
              onClick={onClose}
              className="w-full rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Done
            </button>
          </div>
        ) : (
          /* Form state */
          <>
            <div className="mb-5 flex items-start justify-between">
              <h2
                id="booking-modal-title"
                className="text-lg font-bold text-gray-900 dark:text-gray-100"
              >
                Book a Mechanic
              </h2>
              <button
                onClick={onClose}
                aria-label="Close booking form"
                className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              <div>
                <label
                  htmlFor="customer_name"
                  className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Full Name <span aria-hidden="true" className="text-red-500">*</span>
                </label>
                <input
                  ref={firstInputRef}
                  id="customer_name"
                  type="text"
                  required
                  value={form.customer_name}
                  onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                  placeholder="Your full name"
                  className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </div>

              <div>
                <label
                  htmlFor="phone_number"
                  className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Phone Number <span aria-hidden="true" className="text-red-500">*</span>
                </label>
                <input
                  id="phone_number"
                  type="tel"
                  required
                  value={form.phone_number}
                  onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                  placeholder="+91 99999 99999"
                  className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </div>

              <div>
                <label
                  htmlFor="preferred_slot"
                  className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Preferred Date & Time <span aria-hidden="true" className="text-red-500">*</span>
                </label>
                <input
                  id="preferred_slot"
                  type="datetime-local"
                  required
                  value={form.preferred_slot}
                  onChange={(e) => setForm({ ...form, preferred_slot: e.target.value })}
                  className="w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
                />
              </div>

              {bookingError && (
                <p className="text-xs text-red-500" role="alert">
                  {bookingError}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting || !form.customer_name || !form.phone_number || !form.preferred_slot}
                className="w-full rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSubmitting ? "Confirming…" : "Confirm Booking"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
