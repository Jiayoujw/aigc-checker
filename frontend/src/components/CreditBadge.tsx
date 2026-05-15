import { useState, useEffect, useCallback } from 'react';
import { Coins, Zap, RefreshCw } from 'lucide-react';
import { getCreditsStats } from '../services/api';
import type { CreditStats } from '../types';
import { useAuth } from '../context/AuthContext';

export default function CreditBadge() {
  const { isLoggedIn } = useAuth();
  const [stats, setStats] = useState<CreditStats | null>(null);
  const [open, setOpen] = useState(false);

  const fetch = useCallback(async () => {
    if (!isLoggedIn) return;
    try {
      const s = await getCreditsStats();
      setStats(s);
    } catch { /* ignore */ }
  }, [isLoggedIn]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  if (!isLoggedIn || !stats) return null;

  const detectRemaining = stats.daily_detect_total - stats.daily_detect_used;
  const rewriteRemaining = stats.daily_rewrite_total - stats.daily_rewrite_used;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700
                   bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <Coins className="w-3.5 h-3.5 text-amber-500" />
        <span className="text-gray-600 dark:text-gray-400">
          检测 <span className="font-medium text-gray-800 dark:text-gray-200">{detectRemaining}</span>
        </span>
        <span className="text-gray-300 dark:text-gray-600">|</span>
        <span className="text-gray-600 dark:text-gray-400">
          改写 <span className="font-medium text-gray-800 dark:text-gray-200">{rewriteRemaining}</span>
        </span>
        {stats.purchased_credits > 0 && (
          <span className="text-amber-500 font-medium">+{stats.purchased_credits}</span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-20 w-64 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                <Coins className="w-4 h-4 text-amber-500" />
                额度中心
              </h4>
              <button
                onClick={fetch}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                title="刷新"
              >
                <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
              </button>
            </div>

            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500 flex items-center gap-1">
                  <Zap className="w-3 h-3 text-blue-400" />
                  每日免费检测
                </span>
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {detectRemaining} / {stats.daily_detect_total}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500 flex items-center gap-1">
                  <Zap className="w-3 h-3 text-purple-400" />
                  每日免费改写
                </span>
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {rewriteRemaining} / {stats.daily_rewrite_total}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-100 dark:border-gray-800">
                <span className="text-gray-500">购买积分</span>
                <span className="font-medium text-amber-500">{stats.purchased_credits} 分</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">累计检测</span>
                <span className="font-medium text-gray-600 dark:text-gray-400">{stats.total_detections}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">累计改写</span>
                <span className="font-medium text-gray-600 dark:text-gray-400">{stats.total_rewrites}</span>
              </div>
            </div>

            <p className="text-xs text-gray-400 mt-3 pt-2 border-t border-gray-100 dark:border-gray-800">
              每日0点重置 · 支持积分购买
            </p>
          </div>
        </>
      )}
    </div>
  );
}
