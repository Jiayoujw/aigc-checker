interface Props {
  score: number;
  label: string;
  size?: 'sm' | 'md';
}

function getColor(score: number): string {
  if (score < 30) return '#22c55e';
  if (score < 70) return '#eab308';
  return '#ef4444';
}

function getLabel(score: number): string {
  if (score < 30) return '低';
  if (score < 70) return '中';
  return '高';
}

export default function ScoreGauge({ score, label, size = 'md' }: Props) {
  const color = getColor(score);
  const r = size === 'sm' ? 36 : 50;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const fontSize = size === 'sm' ? 'text-lg' : 'text-2xl';

  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-xs text-gray-500 font-medium">{label}</span>
      <div className="relative inline-flex items-center justify-center">
        <svg width={(r + 8) * 2} height={(r + 8) * 2} className="-rotate-90">
          <circle
            cx={r + 8}
            cy={r + 8}
            r={r}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="6"
          />
          <circle
            cx={r + 8}
            cy={r + 8}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className={`${fontSize} font-bold`} style={{ color }}>
            {Math.round(score)}
          </span>
          <span className="text-xs" style={{ color }}>
            {getLabel(score)}
          </span>
        </div>
      </div>
    </div>
  );
}
