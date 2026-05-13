import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ScanEye, PenLine, Download,
  LayoutDashboard, Gauge, Brain, BarChart3,
  AlertTriangle, ChevronRight,
} from 'lucide-react';
import type {
  DetectResponse,
  CompareResponse,
  RewriteResponse,
} from '../types';
import { detectAigc, detectCompare, rewriteText } from '../services/api';
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

type Tab = 'detect' | 'rewrite';
type InputMode = 'text' | 'file';

const tabs: { key: Tab; label: string; icon: typeof ScanEye }[] = [
  { key: 'detect', label: 'AIGC检测', icon: ScanEye },
  { key: 'rewrite', label: '降AIGC改写', icon: PenLine },
];

function FeatureBar({ label, value, detail }: { label: string; value: number; detail?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  const color = pct < 30 ? 'bg-green-500' : pct < 70 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium text-gray-700 dark:text-gray-300">{pct.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {detail && <p className="text-xs text-gray-400">{detail}</p>}
    </div>
  );
}

function ParagraphHeatmap({ paragraphs }: { paragraphs: DetectResponse['paragraphs'] }) {
  const [expanded, setExpanded] = useState(false);
  if (!paragraphs || paragraphs.length === 0) return null;

  const visible = expanded ? paragraphs : paragraphs.slice(0, 6);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
          <BarChart3 className="w-3.5 h-3.5" />
          段落热力图
        </h4>
        {paragraphs.length > 6 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"
          >
            {expanded ? '收起' : `查看全部 (${paragraphs.length})`}
            {expanded ? <ChevronRight className="w-3 h-3 rotate-90" /> : <ChevronRight className="w-3 h-3" />}
          </button>
        )}
      </div>

      <div className="space-y-1">
        {visible.map((p) => {
          const color =
            p.level === 'high' ? 'border-red-400 bg-red-50 dark:bg-red-950/20' :
            p.level === 'medium' ? 'border-amber-400 bg-amber-50 dark:bg-amber-950/20' :
            'border-green-400 bg-green-50 dark:bg-green-950/20';
          const barColor =
            p.level === 'high' ? 'bg-red-500' :
            p.level === 'medium' ? 'bg-amber-500' :
            'bg-green-500';

          return (
            <div key={p.index} className={`border-l-2 rounded-r-lg p-2.5 text-xs ${color}`}>
              <div className="flex items-center justify-between gap-3">
                <span className="text-gray-400 font-mono w-6">#{p.index + 1}</span>
                <span className="flex-1 text-gray-700 dark:text-gray-300 truncate">
                  {p.text.slice(0, 100)}{p.text.length > 100 ? '...' : ''}
                </span>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="w-12 h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${p.fused_score}%` }} />
                  </div>
                  <span className={`font-bold w-8 text-right ${
                    p.level === 'high' ? 'text-red-600' :
                    p.level === 'medium' ? 'text-amber-600' :
                    'text-green-600'
                  }`}>
                    {p.fused_score.toFixed(0)}
                  </span>
                </div>
              </div>
              {p.stat_details.length > 0 && (
                <div className="mt-1 text-gray-400 pl-6 truncate">
                  {p.stat_details[0]}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatPanel({ stat, fused }: { stat: DetectResponse['statistical_analysis']; fused: DetectResponse['fused_result'] }) {
  if (!stat && !fused) return null;

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
        <Gauge className="w-3.5 h-3.5" />
        多维特征分析
      </h4>

      {stat && (
        <div className="space-y-2.5">
          <FeatureBar label="困惑度" value={stat.perplexity} detail="文本可预测性" />
          <FeatureBar label="句式突发度" value={stat.burstiness} detail="句长变化程度" />
          <FeatureBar label="词汇多样性" value={stat.lexical_diversity} detail="用词重复度" />
          <FeatureBar label="模板匹配" value={Math.min(100, stat.template_hits * 12)} detail={`${stat.template_hits}处AI常见表达`} />
        </div>
      )}

      {fused && (
        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-gray-100 dark:border-gray-800">
          {[
            ['LLM语义', fused.llm_score, fused.llm_score < 30 ? 'text-green-600' : fused.llm_score < 70 ? 'text-amber-600' : 'text-red-600'],
            ['统计分析', fused.statistical_score, fused.statistical_score < 30 ? 'text-green-600' : fused.statistical_score < 70 ? 'text-amber-600' : 'text-red-600'],
            ['融合判定', fused.combined_score, 'text-blue-600 font-bold'],
          ].map(([label, val, cls]) => (
            <div key={label as string} className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2 text-center">
              <p className="text-xs text-gray-400">{label}</p>
              <p className={`text-lg ${cls}`}>{(val as number).toFixed(0)}</p>
            </div>
          ))}
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-2 text-center">
            <p className="text-xs text-gray-400">置信度</p>
            <p className={`text-sm font-medium ${
              fused.confidence === 'high' ? 'text-green-600' :
              fused.confidence === 'medium' ? 'text-amber-600' : 'text-red-600'
            }`}>
              {fused.confidence === 'high' ? '高' : fused.confidence === 'medium' ? '中' : '低'}
            </p>
          </div>
        </div>
      )}

      {stat?.details && stat.details.length > 0 && (
        <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 mb-1">特征详情:</p>
          {stat.details.slice(0, 3).map((d, i) => (
            <p key={i} className="text-xs text-gray-400">• {d}</p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Workbench() {
  const [text, setText] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('detect');
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [detectLoading, setDetectLoading] = useState(false);
  const [rewriteLoading, setRewriteLoading] = useState(false);

  const [mode, setMode] = useState<'general' | 'academic' | 'resume' | 'social_media'>('general');
  const [intensity, setIntensity] = useState<'light' | 'medium' | 'deep'>('medium');
  const [preserveTerms, setPreserveTerms] = useState(false);
  const [compareMode, setCompareMode] = useState(false);

  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [rewriteResult, setRewriteResult] = useState<RewriteResponse | null>(null);

  const canSubmit = text.length >= 50;
  const isLoading = detectLoading || rewriteLoading;

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
        } as Parameters<typeof detectCompare>[0]);
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
      const payload: Record<string, unknown> = { type: 'detect' };
      if (detectResult) {
        Object.assign(payload, detectResult);
        payload.char_count = text.length;
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
  }, [detectResult, rewriteResult, text]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        activeTab === 'detect'
          ? handleDetect()
          : handleRewrite();
      }
    },
    [activeTab, handleDetect, handleRewrite]
  );

  const ActiveIcon = tabs.find(t => t.key === activeTab)?.icon || ScanEye;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950" onKeyDown={handleKeyDown}>
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 md:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <LayoutDashboard className="w-5 h-5 text-blue-500" />
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
                <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Brain className="w-3.5 h-3.5" />
                  双模型对比
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
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                disabled={isLoading}
                className={`flex-1 py-3 rounded-xl font-medium text-sm transition-all
                           disabled:opacity-50 disabled:cursor-not-allowed
                           active:scale-[0.98] flex items-center justify-center gap-1.5
                           ${
                             activeTab === tab.key
                               ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                               : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800'
                           }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Action button */}
        <div className="mb-8">
          <button
            onClick={
              activeTab === 'detect'
                ? handleDetect
                : handleRewrite
            }
            disabled={!canSubmit || isLoading}
            className="w-full py-4 rounded-xl font-semibold text-white
                       bg-gradient-to-r from-blue-500 to-blue-600
                       hover:from-blue-600 hover:to-blue-700
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-lg shadow-blue-500/25
                       active:scale-[0.99] flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                处理中...
              </>
            ) : (
              <>
                <ActiveIcon className="w-5 h-5" />
                开始{tabs.find((t) => t.key === activeTab)?.label}
              </>
            )}
          </button>
        </div>

        {/* Results */}
        <AnimatePresence mode="wait">
          {/* === AIGC DETECTION RESULT (with paragraph + stats) === */}
          {activeTab === 'detect' && compareResult && (
            <motion.div
              key="compare-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm mb-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-blue-500" />
                  双模型对比检测
                </h3>
                <button
                  onClick={handleExport}
                  className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                             text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                             flex items-center gap-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  导出报告
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
                <div className={`mt-4 p-3 rounded-lg text-center ${
                  compareResult.consensus.agreement === 'high'
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : compareResult.consensus.agreement === 'medium'
                    ? 'bg-amber-50 dark:bg-amber-900/20'
                    : 'bg-red-50 dark:bg-red-900/20'
                }`}>
                  <span className="text-xs">
                    一致性: {' '}
                    {compareResult.consensus.agreement === 'high' ? '高' : compareResult.consensus.agreement === 'medium' ? '中' : '低'}
                    {' · '}平均分: {compareResult.consensus.avg_score}%
                    {compareResult.consensus.diff !== undefined && ` · 差异: ${compareResult.consensus.diff}%`}
                  </span>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'detect' && detectResult && (
            <motion.div
              key="detect-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Score + main info */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <ScanEye className="w-4 h-4 text-blue-500" />
                    AIGC检测结果
                    {detectResult.confidence && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        detectResult.confidence === 'high'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : detectResult.confidence === 'medium'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {detectResult.confidence === 'high' ? '高置信度' : detectResult.confidence === 'medium' ? '中置信度' : '低置信度'}
                      </span>
                    )}
                    {detectResult.mixed_content && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        混合内容
                      </span>
                    )}
                  </h3>
                  <div className="flex items-center gap-2">
                    {detectResult.detection_time_ms && (
                      <span className="text-xs text-gray-400">{detectResult.detection_time_ms}ms</span>
                    )}
                    <button
                      onClick={handleExport}
                      className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                                 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                                 flex items-center gap-1"
                    >
                      <Download className="w-3.5 h-3.5" />
                      导出报告
                    </button>
                  </div>
                </div>

                <div className="flex flex-col md:flex-row items-start gap-8">
                  <ScoreGauge score={detectResult.score} label="AI生成概率" />
                  <div className="flex-1 space-y-4 min-w-0">
                    {/* Score distribution for paragraph analysis */}
                    {detectResult.score_distribution && (
                      <div className="flex gap-3 text-xs">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 rounded bg-green-500" />
                          <span className="text-gray-500">低: {detectResult.score_distribution.low}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 rounded bg-amber-500" />
                          <span className="text-gray-500">中: {detectResult.score_distribution.medium}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 rounded bg-red-500" />
                          <span className="text-gray-500">高: {detectResult.score_distribution.high}</span>
                        </div>
                        {detectResult.paragraph_count && (
                          <span className="text-gray-400">共 {detectResult.paragraph_count} 段</span>
                        )}
                      </div>
                    )}

                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {detectResult.analysis}
                    </p>

                    <HighlightText segments={detectResult.suspicious_segments} />
                  </div>
                </div>
              </div>

              {/* Paragraph heatmap (for long text) */}
              {detectResult.paragraphs && detectResult.paragraphs.length > 1 && (
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                  <ParagraphHeatmap paragraphs={detectResult.paragraphs} />
                </div>
              )}

              {/* Statistical & fusion panel */}
              {(detectResult.statistical_analysis || detectResult.fused_result) && (
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                  <StatPanel
                    stat={detectResult.statistical_analysis}
                    fused={detectResult.fused_result}
                  />
                </div>
              )}
            </motion.div>
          )}

          {/* Rewrite result */}
          {activeTab === 'rewrite' && rewriteResult && (
            <motion.div
              key="rewrite-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <PenLine className="w-4 h-4 text-blue-500" />
                    降AIGC改写结果
                  </h3>
                  <button
                    onClick={handleExport}
                    className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                               text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                               flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" />
                    导出报告
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
        {!detectResult && !rewriteResult && (
          <div className="text-center py-16 text-gray-400">
            <ScanEye className="w-12 h-12 mx-auto mb-4 opacity-40" />
            <p className="text-sm">输入文本后开始分析</p>
          </div>
        )}
      </main>
    </div>
  );
}
