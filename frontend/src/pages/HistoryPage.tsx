import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { getHistory, deleteHistory } from '../services/api';
import type { HistoryRecord } from '../types';
import Navbar from '../components/Navbar';
import { toast } from '../components/Toast';

const icons: Record<string, string> = {
  detect: '🔍',
  plagiarism: '📑',
  rewrite: '✏️',
};

const labels: Record<string, string> = {
  detect: 'AIGC检测',
  plagiarism: '查重检测',
  rewrite: '降AIGC改写',
};

export default function HistoryPage() {
  const { isLoggedIn } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [loading, setLoading] = useState(false);

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

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Navbar />
        <main className="max-w-5xl mx-auto px-6 py-8">
          <div className="text-center py-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <p className="text-4xl mb-4">{'📋'}</p>
              <p className="text-gray-500 dark:text-gray-400 mb-2">
                登录后即可查看检测历史记录
              </p>
              <Link
                to="/login"
                className="text-sm text-blue-500 hover:text-blue-600"
              >
                前往登录
              </Link>
            </motion.div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 md:px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            历史记录
          </h2>
          <div className="flex gap-1">
            {['', 'detect', 'plagiarism', 'rewrite'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  filter === f
                    ? 'bg-blue-500 text-white'
                    : 'bg-white dark:bg-gray-900 text-gray-500 border border-gray-200 dark:border-gray-800'
                }`}
              >
                {f ? labels[f] : '全部'}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : records.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-4">{'📭'}</p>
            <p className="text-sm">暂无记录</p>
            <Link
              to="/app"
              className="text-sm text-blue-500 hover:text-blue-600 mt-2 inline-block"
            >
              去检测
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {records.map((r) => (
                <motion.div
                  key={r.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800
                             rounded-xl p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-lg">{icons[r.type] || '📄'}</span>
                      <div>
                        <span className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 px-2 py-0.5 rounded">
                          {labels[r.type]}
                        </span>
                        <span className="text-xs text-gray-400 ml-2">
                          {new Date(r.created_at).toLocaleString('zh-CN')}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(r.id)}
                      className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 line-clamp-2">
                    {r.input_text}
                  </p>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>
    </div>
  );
}
