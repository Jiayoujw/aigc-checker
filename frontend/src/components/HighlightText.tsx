import type { SuspiciousSegment } from '../types';

interface Props {
  segments: SuspiciousSegment[];
}

function getHighlightColor(score: number): string {
  if (score >= 80) return 'bg-red-100 border-red-300';
  if (score >= 50) return 'bg-yellow-100 border-yellow-300';
  return 'bg-orange-50 border-orange-200';
}

export default function HighlightText({ segments }: Props) {
  if (segments.length === 0) {
    return (
      <p className="text-sm text-green-600 bg-green-50 rounded-lg p-3">
        未检测到明显AI生成痕迹
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500 font-medium">可疑段落标注：</p>
      {segments.map((seg, i) => (
        <div
          key={i}
          className={`border rounded-lg p-3 ${getHighlightColor(seg.score)}`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-gray-600">
              段落 {i + 1}
            </span>
            <span className="text-xs font-bold text-red-500">
              AI概率 {Math.round(seg.score)}%
            </span>
          </div>
          <p className="text-sm text-gray-800 leading-relaxed">{seg.text}</p>
          <p className="text-xs text-gray-500 mt-1 italic">{seg.reason}</p>
        </div>
      ))}
    </div>
  );
}
