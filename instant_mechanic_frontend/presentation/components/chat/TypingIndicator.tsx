export default function TypingIndicator() {
  return (
    <div
      className="flex items-center gap-2 px-4 py-2"
      role="status"
      aria-label="Assistant is typing"
    >
      <div className="flex h-8 max-w-[80px] items-center justify-center gap-1 rounded-2xl rounded-bl-none bg-gray-100 px-4 dark:bg-gray-700">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-400"
            style={{ animationDelay: `${i * 150}ms` }}
            aria-hidden="true"
          />
        ))}
      </div>
      <span className="sr-only">Instant Mechanic is typing…</span>
    </div>
  );
}
