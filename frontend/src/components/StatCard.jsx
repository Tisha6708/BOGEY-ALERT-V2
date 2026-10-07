export default function StatCard({
  label,
  value,
  description,
  icon: Icon,
  danger = false,
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            {label}
          </p>

          <p
            className={`mt-3 text-3xl font-bold ${
              danger ? "text-red-400" : "text-white"
            }`}
          >
            {value}
          </p>

          <p className="mt-2 text-xs text-slate-500">{description}</p>
        </div>

        {Icon && (
          <div
            className={`rounded-lg p-3 ${
              danger ? "bg-red-500/10" : "bg-cyan-500/10"
            }`}
          >
            <Icon
              size={20}
              className={danger ? "text-red-400" : "text-cyan-400"}
            />
          </div>
        )}
      </div>
    </div>
  );
}