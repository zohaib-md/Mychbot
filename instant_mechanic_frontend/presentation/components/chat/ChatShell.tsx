"use client";

import { useState } from "react";
import { useChat } from "@/application/hooks/useChat";
import { useUpload } from "@/application/hooks/useUpload";
import MessageList from "./MessageList";
import InputBar from "./InputBar";
import DiagnosisCard from "@/presentation/components/diagnosis/DiagnosisCard";
import BookingCTA from "@/presentation/components/booking/BookingCTA";
import BookingModal from "@/presentation/components/booking/BookingModal";

export default function ChatShell() {
  const {
    messages,
    sendMessage,
    isLoading,
    requiresBooking,
    diagnosis,
    sessionId,
    resetChat,
    appendMessage,
  } = useChat();

  const { uploadFile, isUploading, uploadError } = useUpload(sessionId);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [isBooked, setIsBooked] = useState(false);

  const handleFileSelect = async (file: File) => {
    const ok = await uploadFile(file);
    if (ok) {
      appendMessage(
        "user",
        `📎 Attached ${file.name} — it will be analysed with your diagnosis.`,
      );
    }
    return ok;
  };

  const handleNewChat = () => {
    resetChat();
    setIsBooked(false);
    setShowBookingModal(false);
  };

  return (
    <div className="flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-lg"
            aria-hidden="true"
          >
            🔧
          </div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 dark:text-gray-100">
              Instant Mechanic
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              AI Car Diagnostic Assistant
            </p>
          </div>
        </div>
        <button
          onClick={handleNewChat}
          aria-label="Start a new conversation"
          className="rounded-lg px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
        >
          New Chat
        </button>
      </header>

      {/* Message list — fills available space */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Diagnosis card — shown only when a diagnosis is available */}
      {diagnosis && <DiagnosisCard result={diagnosis} />}

      {/* Book Mechanic CTA — shown only when backend flags requires_booking */}
      {requiresBooking && !isBooked && !showBookingModal && (
        <BookingCTA onClick={() => setShowBookingModal(true)} />
      )}

      {/* Input bar */}
      <InputBar
        onSend={sendMessage}
        onFileSelect={handleFileSelect}
        disabled={isLoading}
        isUploading={isUploading}
        uploadError={uploadError}
      />

      {/* Booking modal — rendered as portal-like overlay */}
      {showBookingModal && (
        <BookingModal
          sessionId={sessionId}
          onClose={() => setShowBookingModal(false)}
          onConfirmed={() => setIsBooked(true)}
        />
      )}
    </div>
  );
}
