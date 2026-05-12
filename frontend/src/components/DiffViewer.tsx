import { useState } from 'react';
import { toast } from './Toast';

interface Props {
  original: string;
  rewritten: string;
  changesSummary: string;
  newScore: number;
}

export default function DiffViewer({
  original,
  rewritten,
  changesSummary,
  newScore,
}: Props) {
  const [showOriginal, setShowOriginal] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(rewritten);
      toast('已复制到剪贴板', 'success');
    } catch {
      toast('复制失败', 'error');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">改写结果：</p>
        <div className="flex gap-2">
          <button
            onClick={() => setShowOriginal(!showOriginal)}
            className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600
                       text-gray-600 dark:text-gray-400
                       hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            {showOriginal ? '隐藏原文' : '对比原文'}
          </button>
          <button
            onClick={copyToClipboard}
            className="text-xs px-3 py-1 rounded bg-blue-500 text-white
                       hover:bg-blue-600 transition-colors"
          >
            复制
          </button>
        </div>
      </div>

      {changesSummary && (
        <p className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded p-2">
          {changesSummary}
        </p>
      )}

      {newScore >= 0 && (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500 dark:text-gray-400">改写后AIGC概率：</span>
          <span
            className={`font-bold ${
              newScore < 30
                ? 'text-green-500'
                : newScore < 70
                  ? 'text-yellow-500'
                  : 'text-red-500'
            }`}
          >
            {Math.round(newScore)}%
          </span>
        </div>
      )}

      <div
        className={`grid ${showOriginal ? 'grid-cols-1 md:grid-cols-2 gap-3' : 'grid-cols-1'}`}
      >
        {showOriginal && (
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">原文</p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed max-h-80 overflow-y-auto">
              {original}
            </div>
          </div>
        )}
        <div>
          {showOriginal && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">改写后</p>
          )}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg p-3 text-sm text-gray-800 dark:text-gray-200 leading-relaxed max-h-80 overflow-y-auto">
            {rewritten}
          </div>
        </div>
      </div>
    </div>
  );
}
