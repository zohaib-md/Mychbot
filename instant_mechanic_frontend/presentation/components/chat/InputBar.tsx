"use client";

import { useRef, useState, KeyboardEvent } from "react";

interface InputBarProps {
  onSend: (message: string) => void;
  onFileSelect: (file: File) => Promise<boolean>;
  disabled?: boolean;
  isUploading?: boolean;
  uploadError?: string | null;
}

export default function InputBar({
  onSend,
  onFileSelect,
  disabled = false,
  isUploading = false,
  uploadError = null,
}: InputBarProps) {
  const [text, setText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await onFileSelect(file);
    e.target.value = ""; // reset so same file can be re-selected
  };

  const isDisabled = disabled || isUploading;

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900">
      {uploadError && (
        <p className="mb-2 text-xs text-red-500" role="alert">
          {uploadError}
        </p>
      )}
      <div className="flex items-end gap-2">
        {/* File attach button */}
        <button
          type="button"
          aria-label="Attach file — image, audio or video"
          disabled={isDisabled}
          onClick={() => fileInputRef.current?.click()}
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border border-gray-300 text-gray-500 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-800"
        >
          {isUploading ? (
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-transparent"
              aria-hidden="true"
            />
          ) : (
            <span aria-hidden="true">📎</span>
          )}
        </button>

        {/* Hidden file input — accepts image, audio, video */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,audio/mpeg,audio/wav,video/mp4"
          className="hidden"
          onChange={handleFileChange}
          aria-hidden="true"
          tabIndex={-1}
        />

        {/* Text area */}
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your vehicle issue…"
          rows={1}
          disabled={isDisabled}
          aria-label="Type your message"
          className="flex-1 resize-none rounded-2xl border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
          style={{ maxHeight: "120px" }}
        />

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={isDisabled || !text.trim()}
          aria-label="Send message"
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
          </svg>
        </button>
      </div>
      <p className="mt-1.5 text-center text-xs text-gray-400">
        Press{" "}
        <kbd className="rounded border border-gray-300 px-1 font-mono text-xs">
          Enter
        </kbd>{" "}
        to send ·{" "}
        <kbd className="rounded border border-gray-300 px-1 font-mono text-xs">
          Shift+Enter
        </kbd>{" "}
        for newline
      </p>
    </div>
  );
}
