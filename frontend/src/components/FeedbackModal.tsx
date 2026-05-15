import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, X, Award } from 'lucide-react';
import { submitFeedback } from '../services/api';
import { toast } from './Toast';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  ourPredictedScore: number;
  inputText: string;
  platform?: string;
}

const PLATFORMS = [
  { value: 'cnki', label: '知网 CNKI' },
  { value: 'weipu', label: '维普 Weipu' },
  { value: 'wanfang', label: '万方 Wanfang' },
];

export default function FeedbackModal({ isOpen, onClose, ourPredictedScore, inputText, platform }: Props) {
  const [selectedPlatform, setSelectedPlatform] = useState(platform || 'cnki');
  const [realScore, setRealScore] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ error: number; credits: number } | null>(null);

  const handleSubmit = async () => {
    const score = parseFloat(realScore);
    if (isNaN(score) || score < 0 || score > 100) {
      toast('请输入有效的分数 (0-100)', 'error');
      return;
    }

    setLoading(true);
    try {
      const res = await submitFeedback({
        platform: selectedPlatform as 'cnki' | 'weipu' | 'wanfang',
        our_predicted_score: ourPredictedScore,
        real_score: score,
        input_text: inputText.slice(0, 5000),
        mode: 'general',
      });
      setResult({ error: res.prediction_error, credits: res.credits_earned });
      toast(res.message, 'success');
    } catch (e) {
      toast(e instanceof Error ? e.message : '反馈提交失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/40" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-2xl p-6 w-full max-w-md"
          >
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1 flex items-center gap-2">
              <Send className="w-5 h-5 text-blue-500" />
              反馈真实平台分数
            </h3>
            <p className="text-xs text-gray-500 mb-5">
              提交真实平台检测分数帮助我们校准模型，每次反馈奖励 <span className="text-amber-500 font-medium">+1 积分</span>
            </p>

            {result ? (
              <div className="text-center py-6 space-y-3">
                <Award className="w-12 h-12 text-amber-500 mx-auto" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  预测误差: <span className={`font-bold ${Math.abs(result.error) <= 10 ? 'text-green-500' : 'text-amber-500'}`}>
                    {result.error > 0 ? '+' : ''}{result.error.toFixed(1)}%
                  </span>
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  获得积分: <span className="font-bold text-amber-500">+{result.credits}</span>
                </p>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  完成
                </button>
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">检测平台</label>
                    <div className="flex gap-2">
                      {PLATFORMS.map((p) => (
                        <button
                          key={p.value}
                          onClick={() => setSelectedPlatform(p.value)}
                          className={`flex-1 py-2 text-xs rounded-lg border transition-colors ${
                            selectedPlatform === p.value
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                              : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300'
                          }`}
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                      <p className="text-xs text-gray-400 mb-1">我们预测分</p>
                      <p className="text-xl font-bold text-blue-500">{ourPredictedScore.toFixed(0)}</p>
                    </div>
                    <div>
                      <label className="text-xs text-gray-500 mb-1 block">平台真实分</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={realScore}
                        onChange={(e) => setRealScore(e.target.value)}
                        placeholder="0-100"
                        className="w-full px-3 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-700
                                   bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                                   focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={onClose}
                    className="flex-1 py-2.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading || !realScore}
                    className="flex-1 py-2.5 text-sm rounded-lg bg-blue-500 text-white
                               hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed
                               transition-colors flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    提交反馈
                  </button>
                </div>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
