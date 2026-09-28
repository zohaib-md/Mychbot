interface BookingCTAProps {
  onClick: () => void;
}

export default function BookingCTA({ onClick }: BookingCTAProps) {
  return (
    <div className="mx-4 mb-3">
      <button
        type="button"
        onClick={onClick}
        className="w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 active:scale-[0.98] dark:focus:ring-offset-gray-900"
        aria-label="Book a verified Instant Mechanic for an on-site visit"
      >
        🔧 Book a Mechanic — Get On-Site Help
      </button>
    </div>
  );
}
