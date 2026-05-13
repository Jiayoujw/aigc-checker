import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ScanEye, PenLine, Clock, Trash2,
  ChevronRight, Filter, Search, Inbox, ArrowRight,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getHistory, deleteHistory } from '../services/api';
import type { HistoryRecord } from '../types';
import Navbar from '../components/Navbar';
import { toast } from '../components/Toast';

const typeConfig: Record<string, { icon: typeof ScanEye; label: string; color: string; bg: string }> = {
  detect: { icon: ScanEye, label: 'AIGC检测', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-950/30' },
  rewrite: { icon: PenLine, label: '降AIGC改写', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-950/30' },
};

function parseResultJson(json: string): { score?: number; level?: string; combined_score?: number } | null {
  try { return JSON.parse(json); } catch { return null; }
}

const filters = [
  { key: '', label: '全部', icon: Filter },
  { key: 'detect', label: 'AIGC检测', icon: ScanEye },
  { key: 'rewrite', label: '降AIGC改写', icon: PenLine },
];

export default function HistoryPage() {
  const { isLoggedIn } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (isLoggedIn) {
      setLoading(true);
      getHistory(filter || undefined)
        .then(setRecords)
        .catch(() => toast('加载历史失败', 'error'))
        .finally(() => setLoading(false));
    }
  }, [isLoggedIn, filter]);

  const handleDelete = async (id: string) => {
    try {
      await deleteHistory(id);
      setRecords((prev) => prev.filter((r) => r.id !== id));
      toast('已删除', 'success');
    } catch {
      toast('删除失败', 'error');
    }
  };

  const filteredRecords = search
    ? records.filter(r => r.input_text.toLowerCase().includes(search.toLowerCase()))
    : records;

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Navbar />
        <main className="max-w-2xl mx-auto px-6 py-24 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="w-20 h-20 rounded-2xl bg-blue-50 dark:bg-blue-950/30 flex items-center justify-center mx-auto mb-6">
              <Clock className="w-10 h-10 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">登录查看历史</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-8">
              登录后即可查看和管理你的检测历史记录
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-500 text-white font-medium
                         hover:bg-blue-600 transition-all shadow-lg shadow-blue-500/25 active:scale-[0.98]"
            >
              前往登录
              <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 md:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Clock className="w-6 h-6 text-blue-500" />
              历史记录
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {records.length} 条检测记录
            </p>
          </div>

          <div className="flex gap-2">
            {filters.map((f) => {
              const Icon = f.icon;
              return (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-all ${
                    filter === f.key
                      ? 'bg-blue-500 text-white shadow-md shadow-blue-500/20'
                      : 'bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {f.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search */}
        {records.length > 5 && (
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索历史记录..."
              className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                         bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none
                         placeholder-gray-400 transition-all"
            />
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse bg-white dark:bg-gray-900 rounded-xl p-5 border border-gray-200 dark:border-gray-800">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-800" />
                  <div className="h-4 w-20 bg-gray-200 dark:bg-gray-800 rounded" />
                  <div className="h-3 w-32 bg-gray-100 dark:bg-gray-800 rounded" />
                </div>
                <div className="h-4 w-3/4 bg-gray-100 dark:bg-gray-800 rounded" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && records.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20"
          >
            <div className="w-20 h-20 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-6">
              <Inbox className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold mb-2">暂无记录</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              开始检测后，你的历史记录将显示在这里
            </p>
            <Link
              to="/app"
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-medium
                         hover:bg-blue-600 transition-all active:scale-[0.98]"
            >
              去检测
              <ChevronRight className="w-4 h-4" />
            </Link>
          </motion.div>
        )}

        {/* Records list */}
        {!loading && filteredRecords.length > 0 && (
          <div className="space-y-3">
            <AnimatePresence>
              {filteredRecords.map((r, idx) => {
                const config = typeConfig[r.type] || typeConfig.detect;
                const Icon = config.icon;
                const result = parseResultJson(r.result_json);
                const score = result?.combined_score ?? result?.score;

                return (
                  <motion.div
                    key={r.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: idx * 0.03 }}
                    className="group bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800
                               rounded-xl p-5 shadow-sm hover:shadow-md hover:border-gray-300
                               dark:hover:border-gray-700 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        <div className={`w-9 h-9 rounded-xl ${config.bg} flex items-center justify-center flex-shrink-0`}>
                          <Icon className={`w-5 h-5 ${config.color}`} />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-xs font-medium px-2 py-0.5 rounded-md ${config.bg} ${config.color}`}>
                              {config.label}
                            </span>
                            {score !== undefined && (
                              <span className={`text-xs font-bold ${
                                score >= 70 ? 'text-red-600' : score >= 30 ? 'text-amber-600' : 'text-emerald-600'
                              }`}>
                                {score.toFixed(0)}%
                              </span>
                            )}
                            <span className="text-xs text-gray-400">
                              {new Date(r.created_at).toLocaleString('zh-CN', {
                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                              })}
                            </span>
                          </div>

                          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
                            {r.input_text}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() => handleDelete(r.id)}
                        className="flex-shrink-0 p-2 rounded-lg text-gray-400 hover:text-red-500
                                   hover:bg-red-50 dark:hover:bg-red-950/20 opacity-0 group-hover:opacity-100
                                   transition-all"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {/* Search no results */}
        {!loading && search && filteredRecords.length === 0 && records.length > 0 && (
          <div className="text-center py-16 text-gray-400">
            <Search className="w-10 h-10 mx-auto mb-4 opacity-50" />
            <p className="text-sm">未找到匹配 "{search}" 的记录</p>
          </div>
        )}
      </main>
    </div>
  );
}
