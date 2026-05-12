import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  DetectResponse,
  CompareResponse,
  PlagiarismResponse,
  RewriteResponse,
} from '../types';
import { detectAigc, detectCompare, checkPlagiarism, rewriteText } from '../services/api';
import Navbar from '../components/Navbar';
import TextInput from '../components/TextInput';
import ScoreGauge from '../components/ScoreGauge';
import HighlightText from '../components/HighlightText';
import DiffViewer from '../components/DiffViewer';
import FileUpload from '../components/FileUpload';
import { toast } from '../components/Toast';

const API_BASE = import.meta.env.PROD
  ? 'https://aigc-checker.onrender.com/api'
  : '/api';

type Tab = 'detect' | 'rewrite' | 'plagiarism';
type InputMode = 'text' | 'file';

const tabs: { key: Tab; label: string; icon: string }[] = [
  { key: 'detect', label: 'AIGC检测', icon: '🔍' },
  { key: 'rewrite', label: '降AIGC改写', icon: '✏️' },
  { key: 'plagiarism', label: '查重检测', icon: '📑' },
];

export default function Workbench() {
  const [text, setText] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('detect');
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [detectLoading, setDetectLoading] = useState(false);
  const [rewriteLoading, setRewriteLoading] = useState(false);
  const [plagiarismLoading, setPlagiarismLoading] = useState(false);

  const [mode, setMode] = useState<'general' | 'academic' | 'resume' | 'social_media'>('general');
  const [intensity, setIntensity] = useState<'light' | 'medium' | 'deep'>('medium');
  const [preserveTerms, setPreserveTerms] = useState(false);
  const [compareMode, setCompareMode] = useState(false);

  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [rewriteResult, setRewriteResult] =
    useState<RewriteResponse | null>(null);
  const [plagiarismResult, setPlagiarismResult] =
    useState<PlagiarismResponse | null>(null);

  const canSubmit = text.length >= 50;
  const isLoading = detectLoading || rewriteLoading || plagiarismLoading;

  const handleDetect = useCallback(async () => {
    if (!canSubmit) return;
    setDetectLoading(true);
    setCompareResult(null);
    setDetectResult(null);
    try {
      if (compareMode) {
        const res = await detectCompare({
          text, provider: 'auto',
          mode,
        } as unknown as Parameters<typeof detectCompare>[0]);
        setCompareResult(res);
      } else {
        const res = await detectAigc({ text, provider: 'auto', mode });
        setDetectResult(res);
      }
    } catch (e) {
      toast(e instanceof Error ? e.message : '检测失败', 'error');
    } finally {
      setDetectLoading(false);
    }
  }, [text, canSubmit, mode, compareMode]);

  const handlePlagiarism = useCallback(async () => {
    if (!canSubmit) return;
    setPlagiarismLoading(true);
    try {
      const res = await checkPlagiarism({ text });
      setPlagiarismResult(res);
    } catch (e) {
      toast(e instanceof Error ? e.message : '查重失败', 'error');
    } finally {
      setPlagiarismLoading(false);
    }
  }, [text, canSubmit]);

  const handleRewrite = useCallback(async () => {
    if (!canSubmit) return;
    setRewriteLoading(true);
    try {
      const res = await rewriteText({
        text, provider: 'auto', intensity, preserve_terms: preserveTerms,
      });
      setRewriteResult(res);
    } catch (e) {
      toast(e instanceof Error ? e.message : '改写失败', 'error');
    } finally {
      setRewriteLoading(false);
    }
  }, [text, canSubmit]);

  const handleExport = useCallback(async () => {
    try {
      const payload: Record<string, unknown> = {};
      if (detectResult) {
        payload.type = 'detect';
        payload.score = detectResult.score;
        payload.analysis = detectResult.analysis;
        payload.suspicious_segments = detectResult.suspicious_segments;
      } else if (plagiarismResult) {
        payload.type = 'plagiarism';
        payload.similarity_score = plagiarismResult.similarity_score;
        payload.details = plagiarismResult.details;
      } else if (rewriteResult) {
        payload.type = 'rewrite';
        payload.rewritten_text = rewriteResult.rewritten_text;
        payload.changes_summary = rewriteResult.changes_summary;
        payload.score = rewriteResult.new_aigc_score;
      }
      const res = await fetch(`${API_BASE}/export-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('导出失败');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `aigc-report-${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast('报告已下载', 'success');
    } catch {
      toast('导出失败', 'error');
    }
  }, [detectResult, plagiarismResult, rewriteResult]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        activeTab === 'detect'
          ? handleDetect()
          : activeTab === 'rewrite'
            ? handleRewrite()
            : handlePlagiarism();
      }
    },
    [activeTab, handleDetect, handleRewrite, handlePlagiarism]
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950" onKeyDown={handleKeyDown}>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 md:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            工作台
          </h2>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <kbd className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-gray-500">
              Ctrl+Enter
            </kbd>
            <span>快速执行</span>
          </div>
        </div>

        {/* Input area */}
        <div className="mb-6">
          <div className="flex gap-1 mb-3">
            <button
              onClick={() => setInputMode('text')}
              className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${
                inputMode === 'text'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-800'
              }`}
            >
              直接输入
            </button>
            <button
              onClick={() => setInputMode('file')}
              className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${
                inputMode === 'file'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-800'
              }`}
            >
              上传文件
            </button>
          </div>

          <AnimatePresence mode="wait">
            {inputMode === 'text' ? (
              <motion.div
                key="text"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <TextInput value={text} onChange={setText} />
              </motion.div>
            ) : (
              <motion.div
                key="file"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <FileUpload onTextExtracted={setText} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Options bar */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {activeTab === 'detect' && (
            <>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as typeof mode)}
                className="text-xs px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700
                           bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300"
              >
                <option value="general">通用模式</option>
                <option value="academic">论文模式</option>
                <option value="resume">简历模式</option>
                <option value="social_media">自媒体模式</option>
              </select>
              <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={compareMode}
                  onChange={(e) => setCompareMode(e.target.checked)}
                  className="rounded"
                />
                <span className="text-gray-600 dark:text-gray-400">
                  双模型对比 (DeepSeek + OpenAI)
                </span>
              </label>
            </>
          )}
          {activeTab === 'rewrite' && (
            <>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">强度:</span>
                {(['light', 'medium', 'deep'] as const).map((l) => (
                  <button
                    key={l}
                    onClick={() => setIntensity(l)}
                    className={`px-2.5 py-1 text-xs rounded-lg transition-colors ${
                      intensity === l
                        ? 'bg-blue-500 text-white'
                        : 'bg-white dark:bg-gray-900 text-gray-500 border border-gray-200 dark:border-gray-800'
                    }`}
                  >
                    {l === 'light' ? '轻度' : l === 'medium' ? '中度' : '深度'}
                  </button>
                ))}
              </div>
              <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={preserveTerms}
                  onChange={(e) => setPreserveTerms(e.target.checked)}
                  className="rounded"
                />
                <span className="text-gray-600 dark:text-gray-400">
                  保留专业术语
                </span>
              </label>
            </>
          )}
        </div>

        {/* Tab buttons */}
        <div className="flex gap-2 mb-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              disabled={isLoading}
              className={`flex-1 py-3 rounded-xl font-medium text-sm transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed
                         active:scale-[0.98]
                         ${
                           activeTab === tab.key
                             ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                             : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800'
                         }`}
            >
              <span className="mr-1.5">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Action button */}
        <div className="mb-8">
          <button
            onClick={
              activeTab === 'detect'
                ? handleDetect
                : activeTab === 'rewrite'
                  ? handleRewrite
                  : handlePlagiarism
            }
            disabled={!canSubmit || isLoading}
            className="w-full py-4 rounded-xl font-semibold text-white
                       bg-gradient-to-r from-blue-500 to-blue-600
                       hover:from-blue-600 hover:to-blue-700
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-lg shadow-blue-500/25
                       active:scale-[0.99]"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                处理中...
              </span>
            ) : (
              `开始${tabs.find((t) => t.key === activeTab)?.label}`
            )}
          </button>
        </div>

        {/* Results */}
        <AnimatePresence mode="wait">
          {activeTab === 'detect' && compareResult && (
            <motion.div
              key="compare-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    双模型对比检测
                  </h3>
                  <button
                    onClick={handleExport}
                    className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    {'📥'} 导出报告
                  </button>
                </div>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-2">DeepSeek</p>
                    <ScoreGauge score={compareResult.deepseek.score} label="" size="sm" />
                    <p className="text-xs text-gray-500 mt-2">{compareResult.deepseek.analysis}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 mb-2">OpenAI</p>
                    <ScoreGauge score={compareResult.openai.score} label="" size="sm" />
                    <p className="text-xs text-gray-500 mt-2">{compareResult.openai.analysis}</p>
                  </div>
                </div>
                {compareResult.consensus.agreement && (
                  <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
                    <span className="text-xs text-blue-600 dark:text-blue-400">
                      一致性: {compareResult.consensus.agreement === 'high' ? '高' : compareResult.consensus.agreement === 'medium' ? '中' : '低'}
                      {' · '}平均分: {compareResult.consensus.avg_score}%
                      {compareResult.consensus.diff !== undefined && ` · 差异: ${compareResult.consensus.diff}%`}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'detect' && detectResult && (
            <motion.div
              key="detect-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    AIGC检测结果
                  </h3>
                  <button
                    onClick={handleExport}
                    className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    {'📥'} 导出报告
                  </button>
                </div>
                <div className="flex flex-col md:flex-row items-start gap-6">
                  <ScoreGauge score={detectResult.score} label="AI生成概率" />
                  <div className="flex-1 space-y-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {detectResult.analysis}
                    </p>
                    <HighlightText
                      segments={detectResult.suspicious_segments}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'plagiarism' && plagiarismResult && (
            <motion.div
              key="plagiarism-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    查重检测结果
                  </h3>
                  <button
                    onClick={handleExport}
                    className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    {'📥'} 导出报告
                  </button>
                </div>
                <div className="flex flex-col md:flex-row items-start gap-6">
                  <ScoreGauge
                    score={plagiarismResult.similarity_score}
                    label="重复率"
                  />
                  <div className="flex-1 space-y-3">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {plagiarismResult.details}
                    </p>
                    {plagiarismResult.similar_sources.length > 0 &&
                      plagiarismResult.similar_sources.map((src, i) => (
                        <div
                          key={i}
                          className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3"
                        >
                          <p className="text-sm text-gray-800 dark:text-gray-200">
                            {src.text}
                          </p>
                          <div className="flex gap-3 mt-1">
                            <span className="text-xs text-gray-500">
                              {src.reason}
                            </span>
                            <span className="text-xs text-orange-500">
                              {src.possible_source_type}
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'rewrite' && rewriteResult && (
            <motion.div
              key="rewrite-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    降AIGC改写结果
                  </h3>
                  <button
                    onClick={handleExport}
                    className="text-xs px-3 py-1 rounded border border-gray-300 dark:border-gray-600
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    {'📥'} 导出报告
                  </button>
                </div>
                <DiffViewer
                  original={text}
                  rewritten={rewriteResult.rewritten_text}
                  changesSummary={rewriteResult.changes_summary}
                  newScore={rewriteResult.new_aigc_score}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state */}
        {!detectResult && !plagiarismResult && !rewriteResult && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-4">{'📝'}</p>
            <p className="text-sm">输入文本后开始分析</p>
          </div>
        )}
      </main>
    </div>
  );
}
