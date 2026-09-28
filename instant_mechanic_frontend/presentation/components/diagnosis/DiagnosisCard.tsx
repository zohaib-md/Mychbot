import type { DiagnosisResult } from "@/domain/entities";
import UrgencyBadge from "./UrgencyBadge";

interface DiagnosisCardProps {
  result: DiagnosisResult;
}

export default function DiagnosisCard({ result }: DiagnosisCardProps) {
  return (
    <div
      className="mx-4 mb-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800"
      role="region"
      aria-label="Diagnosis result"
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-bold text-gray-900 dark:text-gray-100">
          Diagnosis Result
        </h2>
        <UrgencyBadge level={result.urgency_level} />
      </div>

      {/* Probable Causes */}
      <div className="mb-4">
        <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          Probable Causes
        </h3>
        <ul className="space-y-1" role="list">
          {result.probable_causes.map((cause, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
            >
              <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gray-400" aria-hidden="true" />
              {cause}
            </li>
          ))}
        </ul>
      </div>

      {/* Grid: service + cost */}
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
          <p className="mb-0.5 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Recommended Service
          </p>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {result.recommended_service}
          </p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
          <p className="mb-0.5 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Estimated Cost
          </p>
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {result.estimated_cost_range}
          </p>
        </div>
      </div>

      {/* Mechanic Notes */}
      <div className="rounded-lg border-l-4 border-blue-400 bg-blue-50 p-3 dark:border-blue-500 dark:bg-blue-900/20">
        <p className="mb-0.5 text-xs font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-400">
          Mechanic Notes
        </p>
        <p className="text-sm text-blue-800 dark:text-blue-200">
          {result.mechanic_notes}
        </p>
      </div>
    </div>
  );
}
