export default function MatchScoreBadge({ score }) {
  let colorClasses = 'bg-slate-100 text-slate-700';
  if (score >= 75) colorClasses = 'bg-emerald-100 text-emerald-700';
  else if (score >= 50) colorClasses = 'bg-amber-100 text-amber-700';
  else if (score >= 0) colorClasses = 'bg-rose-100 text-rose-700';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${colorClasses}`}>
      {score}% AI Match
    </span>
  );
}
