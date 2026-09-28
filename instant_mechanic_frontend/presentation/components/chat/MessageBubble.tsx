import type { ChatMessage } from "@/domain/entities";

interface MessageBubbleProps {
  message: ChatMessage;
}

// Render inline **bold** segments (the backend's diagnosis summary uses them).
function renderInline(line: string) {
  return line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") && part.length > 4 ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      part
    ),
  );
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full px-4 py-1 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* Bot avatar */}
      {!isUser && (
        <div
          className="mr-2 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs text-white"
          aria-hidden="true"
        >
          🔧
        </div>
      )}

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "rounded-br-none bg-blue-600 text-white"
            : "rounded-bl-none bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100"
        }`}
        role="article"
        aria-label={`${isUser ? "You" : "Instant Mechanic"}: ${message.content}`}
      >
        {message.content.split("\n").map((line, i) => (
          <p key={i} className={`whitespace-pre-wrap ${i > 0 ? "mt-1" : ""}`}>
            {renderInline(line)}
          </p>
        ))}
      </div>

      {/* User avatar */}
      {isUser && (
        <div
          className="ml-2 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-gray-300 text-xs dark:bg-gray-600"
          aria-hidden="true"
        >
          👤
        </div>
      )}
    </div>
  );
}
