import { UrgencyLevel } from "@/domain/enums";

interface UrgencyBadgeProps {
  level: UrgencyLevel | string;
}

const URGENCY_CONFIG: Record<
  string,
  { label: string; classes: string; icon: string }
> = {
  RED: {
    label: "STOP DRIVING IMMEDIATELY",
    classes:
      "bg-red-100 text-red-800 border border-red-300 dark:bg-red-900/30 dark:text-red-300",
    icon: "🔴",
  },
  YELLOW: {
    label: "CAUTION — LIMIT DRIVING",
    classes:
      "bg-yellow-100 text-yellow-800 border border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-300",
    icon: "🟡",
  },
  GREEN: {
    label: "SAFE TO DRIVE",
    classes:
      "bg-green-100 text-green-800 border border-green-300 dark:bg-green-900/30 dark:text-green-300",
    icon: "🟢",
  },
};

export default function UrgencyBadge({ level }: UrgencyBadgeProps) {
  const config = URGENCY_CONFIG[level] ?? URGENCY_CONFIG.YELLOW;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold tracking-wide ${config.classes}`}
      role="status"
      aria-label={`Urgency: ${config.label}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}
