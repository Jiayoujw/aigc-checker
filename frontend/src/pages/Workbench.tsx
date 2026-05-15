import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ScanEye, PenLine, Download,
  LayoutDashboard, Gauge, Brain, BarChart3,
  AlertTriangle, ChevronRight, MessageSquare,
} from 'lucide-react';
import type {
  DetectResponse,
  CompareResponse,
  RewriteResponse,
  CNKIDetectResponse,
  RewriteV2Response,
  WeipuDetectResponse,
  WanfangDetectResponse,
  CrossPlatformResponse,
} from '../types';
import {
  detectAigc, detectCompare, rewriteText, detectCnki, rewriteV2,
  detectWeipu, detectWanfang, detectAllPlatforms,
} from '../services/api';
import Navbar from '../components/Navbar';
import TextInput from '../components/TextInput';
import ScoreGauge from '../components/ScoreGauge';
import HighlightText from '../components/HighlightText';
import DiffViewer from '../components/DiffViewer';
import FileUpload from '../components/FileUpload';
import CreditBadge from '../components/CreditBadge';
import FeedbackModal from '../components/FeedbackModal';
import ReportRewritePanel from '../components/ReportRewritePanel';
import AccuracyDashboard from '../components/AccuracyDashboard';
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


// CNKI 8-Dimension breakdown component
function CNKIDimensionPanel({ result }: { result: CNKIDetectResponse }) {
  const dims = result.dimension_breakdown;
  const dimLabelMap: Record<string, string> = {
    sentence_structure: '句式结构',
    paragraph_similarity: '段落相似度',
    information_density: '信息密度',
    connectors: '连接词分布',
    terminology: '术语匹配度',
    citations: '引文质量',
    data_specificity: '数据具体性',
    logical_coherence: '逻辑连贯性',
  };

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
        <Gauge className="w-3.5 h-3.5" />
        知网8维特征分析
      </h4>
      <div className="space-y-2">
        {Object.entries(dims).map(([key, dim]) => {
          const isHighRisk = dim.score > 60;
          return (
            <div key={key} className={`p-2.5 rounded-lg border text-xs ${
              isHighRisk
                ? 'border-red-200 bg-red-50 dark:bg-red-950/10 dark:border-red-800'
                : 'border-gray-100 bg-gray-50 dark:bg-gray-800/30 dark:border-gray-700'
            }`}>
              <div className="flex items-center justify-between mb-1">
                <span className={`font-medium ${isHighRisk ? 'text-red-700 dark:text-red-400' : 'text-gray-600 dark:text-gray-400'}`}>
                  {dimLabelMap[key] || key}
                </span>
                <span className={`font-bold ${isHighRisk ? 'text-red-600' : 'text-gray-400'}`}>
                  {dim.score.toFixed(0)}
                </span>
              </div>
              <div className="h-1 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden mb-1">
                <div
                  className={`h-full rounded-full transition-all ${isHighRisk ? 'bg-red-500' : 'bg-blue-400'}`}
                  style={{ width: `${dim.score}%` }}
                />
              </div>
              <p className="text-gray-400 leading-relaxed">{dim.detail}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}


// Rewrite v2 dimension score comparison
function DimensionScoreCompare({
  before,
  after,
}: {
  before: Record<string, number>;
  after: Record<string, number>;
}) {
  const dimLabelMap: Record<string, string> = {
    sentence_structure: '句式结构',
    paragraph_similarity: '段落相似度',
    information_density: '信息密度',
    connectors: '连接词分布',
    terminology: '术语匹配度',
    citations: '引文质量',
    data_specificity: '数据具体性',
    logical_coherence: '逻辑连贯性',
  };

  return (
    <div className="space-y-1.5">
      {Object.keys(before).map((key) => {
        const beforeVal = before[key] || 0;
        const afterVal = after[key] || 0;
        const improvement = beforeVal - afterVal;
        const hasImproved = improvement > 5;

        return (
          <div key={key} className="flex items-center gap-2 text-xs">
            <span className="w-20 text-gray-500 text-right flex-shrink-0">
              {dimLabelMap[key] || key}
            </span>
            <div className="flex-1 flex items-center gap-1">
              <span className="text-gray-400 w-8 text-right">{beforeVal.toFixed(0)}</span>
              <span className="text-gray-300">→</span>
              <span className={`w-8 font-medium ${hasImproved ? 'text-green-600' : 'text-gray-500'}`}>
                {afterVal.toFixed(0)}
              </span>
              {hasImproved && (
                <span className="text-green-500 text-xs ml-1">
                  ↓{improvement.toFixed(0)}
                </span>
              )}
            </div>
            <div className="w-16 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex-shrink-0">
              <div
                className={`h-full rounded-full ${hasImproved ? 'bg-green-500' : 'bg-gray-400'}`}
                style={{ width: `${Math.min(100, Math.max(0, (1 - afterVal / Math.max(1, beforeVal))) * 100)}%` }}
              />
            </div>
          </div>
        );
      })}
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
  const [cnkiResult, setCnkiResult] = useState<CNKIDetectResponse | null>(null);
  const [weipuResult, setWeipuResult] = useState<WeipuDetectResponse | null>(null);
  const [wanfangResult, setWanfangResult] = useState<WanfangDetectResponse | null>(null);
  const [crossPlatformResult, setCrossPlatformResult] = useState<CrossPlatformResponse | null>(null);
  const [rewriteResult, setRewriteResult] = useState<RewriteResponse | null>(null);
  const [rewriteV2Result, setRewriteV2Result] = useState<RewriteV2Response | null>(null);

  // Detection platform selector: 'standard' | 'cnki' | 'weipu' | 'wanfang' | 'all'
  const [detectPlatform, setDetectPlatform] = useState<'standard' | 'cnki' | 'weipu' | 'wanfang' | 'all'>('standard');
  // Rewrite v2 mode (targeted anti-CNKI)
  const [useRewriteV2, setUseRewriteV2] = useState(false);
  const [rewriteTargetScore, setRewriteTargetScore] = useState(25);

  // Feedback modal
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackScore, setFeedbackScore] = useState(0);
  const [feedbackPlatform, setFeedbackPlatform] = useState('cnki');

  const canSubmit = text.length >= 50;
  const isLoading = detectLoading || rewriteLoading;

  const handleDetect = useCallback(async () => {
    if (!canSubmit) return;
    setDetectLoading(true);
    setCompareResult(null);
    setDetectResult(null);
    setCnkiResult(null);
    setWeipuResult(null);
    setWanfangResult(null);
    setCrossPlatformResult(null);
    try {
      if (compareMode) {
        const res = await detectCompare({
          text, provider: 'auto',
          mode,
        } as Parameters<typeof detectCompare>[0]);
        setCompareResult(res);
      } else if (detectPlatform === 'cnki') {
        const res = await detectCnki({ text, mode, provider: 'auto' });
        setCnkiResult(res);
      } else if (detectPlatform === 'weipu') {
        const res = await detectWeipu({ text, mode, provider: 'auto' });
        setWeipuResult(res);
      } else if (detectPlatform === 'wanfang') {
        const res = await detectWanfang({ text, mode, provider: 'auto' });
        setWanfangResult(res);
      } else if (detectPlatform === 'all') {
        const res = await detectAllPlatforms({ text, mode, provider: 'auto' });
        setCrossPlatformResult(res);
      } else {
        const res = await detectAigc({ text, provider: 'auto', mode });
        setDetectResult(res);
      }
    } catch (e) {
      toast(e instanceof Error ? e.message : '检测失败', 'error');
    } finally {
      setDetectLoading(false);
    }
  }, [text, canSubmit, mode, compareMode, detectPlatform]);

  const handleRewrite = useCallback(async () => {
    if (!canSubmit) return;
    setRewriteLoading(true);
    setRewriteResult(null);
    setRewriteV2Result(null);
    try {
      if (useRewriteV2) {
        const res = await rewriteV2({
          text, provider: 'auto', intensity,
          mode, target_score: rewriteTargetScore, max_rounds: 3,
        });
        setRewriteV2Result(res);
      } else {
        const res = await rewriteText({
          text, provider: 'auto', intensity, preserve_terms: preserveTerms,
        });
        setRewriteResult(res);
      }
    } catch (e) {
      toast(e instanceof Error ? e.message : '改写失败', 'error');
    } finally {
      setRewriteLoading(false);
    }
  }, [text, canSubmit, intensity, preserveTerms, useRewriteV2, mode, rewriteTargetScore]);

  const handleExport = useCallback(async () => {
    try {
      const payload: Record<string, unknown> = { type: 'detect' };
      if (crossPlatformResult) {
        payload.type = 'detect_all_platforms';
        Object.assign(payload, crossPlatformResult);
        payload.char_count = text.length;
      } else if (cnkiResult) {
        payload.type = 'detect_cnki';
        Object.assign(payload, cnkiResult);
        payload.char_count = text.length;
      } else if (weipuResult) {
        payload.type = 'detect_weipu';
        Object.assign(payload, weipuResult);
        payload.char_count = text.length;
      } else if (wanfangResult) {
        payload.type = 'detect_wanfang';
        Object.assign(payload, wanfangResult);
        payload.char_count = text.length;
      } else if (detectResult) {
        Object.assign(payload, detectResult);
        payload.char_count = text.length;
      } else if (rewriteV2Result) {
        payload.type = 'rewrite_v2';
        payload.rewritten_text = rewriteV2Result.rewritten_text;
        payload.changes_summary = rewriteV2Result.changes_summary;
        payload.score = rewriteV2Result.new_score;
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
  }, [detectResult, cnkiResult, weipuResult, wanfangResult, crossPlatformResult, rewriteResult, rewriteV2Result, text]);

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
          <div className="flex items-center gap-3">
            <CreditBadge />
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <kbd className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-gray-500">
                Ctrl+Enter
              </kbd>
              <span>快速执行</span>
            </div>
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
              <select
                value={detectPlatform}
                onChange={(e) => {
                  setDetectPlatform(e.target.value as typeof detectPlatform);
                  setCompareMode(false);
                }}
                className="text-xs px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700
                           bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 font-medium"
              >
                <option value="standard">通用检测</option>
                <option value="cnki">知网对标</option>
                <option value="weipu">维普对标</option>
                <option value="wanfang">万方对标</option>
                <option value="all">三平台对比</option>
              </select>
              {detectPlatform === 'standard' && (
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
              )}
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
                  checked={useRewriteV2}
                  onChange={(e) => setUseRewriteV2(e.target.checked)}
                  className="rounded"
                />
                <span className={`flex items-center gap-1 ${useRewriteV2 ? 'text-blue-600 font-medium' : 'text-gray-600 dark:text-gray-400'}`}>
                  <Gauge className="w-3.5 h-3.5" />
                  知网对抗改写
                </span>
              </label>
              {useRewriteV2 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">目标分:</span>
                  <input
                    type="range"
                    min="10"
                    max="40"
                    value={rewriteTargetScore}
                    onChange={(e) => setRewriteTargetScore(Number(e.target.value))}
                    className="w-16"
                  />
                  <span className="text-xs font-mono text-gray-600">{rewriteTargetScore}</span>
                </div>
              )}
              {!useRewriteV2 && (
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
              )}
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
                      onClick={() => { setFeedbackScore(detectResult.score); setFeedbackPlatform('cnki'); setFeedbackOpen(true); }}
                      className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                                 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                                 flex items-center gap-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      反馈真实分
                    </button>
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

          {/* CNKI Detection Result */}
          {activeTab === 'detect' && cnkiResult && (
            <motion.div
              key="cnki-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Main CNKI score card */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-blue-500" />
                    知网对标检测结果
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      cnkiResult.method === 'ml_model'
                        ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                    }`}>
                      {cnkiResult.method === 'ml_model' ? 'ML模型' : '规则引擎'}
                    </span>
                  </h3>
                  <div className="flex items-center gap-2">
                    {cnkiResult.detection_time_ms && (
                      <span className="text-xs text-gray-400">{cnkiResult.detection_time_ms}ms</span>
                    )}
                    <button
                      onClick={() => { setFeedbackScore(cnkiResult.cnki_score); setFeedbackPlatform('cnki'); setFeedbackOpen(true); }}
                      className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600
                                 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors
                                 flex items-center gap-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      反馈真实分
                    </button>
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
                  <ScoreGauge score={cnkiResult.cnki_score} label="预测知网AIGC分数" />
                  <div className="flex-1 space-y-3 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        cnkiResult.level === 'low'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : cnkiResult.level === 'medium'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {cnkiResult.level === 'low' ? '低风险' : cnkiResult.level === 'medium' ? '中风险' : '高风险'}
                      </span>
                      <span className="text-xs text-gray-400">
                        置信度: {(cnkiResult.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    {/* High risk dimensions */}
                    {cnkiResult.high_risk_dimensions.length > 0 && (
                      <div className="p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-800">
                        <p className="text-xs font-medium text-orange-700 dark:text-orange-400 mb-1.5 flex items-center gap-1">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          高风险维度:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {cnkiResult.high_risk_dimensions.map((dim, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400">
                              {dim}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Rewrite suggestions */}
                    {cnkiResult.rewrite_suggestions.length > 0 && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-blue-500 hover:text-blue-600 font-medium">
                          改写建议 ({cnkiResult.rewrite_suggestions.length}条)
                        </summary>
                        <ul className="mt-2 space-y-1.5 pl-3 border-l-2 border-blue-200 dark:border-blue-800">
                          {cnkiResult.rewrite_suggestions.map((s, i) => (
                            <li key={i} className="text-gray-500 dark:text-gray-400 leading-relaxed">
                              {s}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                </div>
              </div>

              {/* Dimension breakdown */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <CNKIDimensionPanel result={cnkiResult} />
              </div>
            </motion.div>
          )}

          {/* Weipu Detection Result */}
          {activeTab === 'detect' && weipuResult && (
            <motion.div
              key="weipu-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-purple-500" />
                    维普对标检测结果
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                      句子级扫描
                    </span>
                  </h3>
                  <div className="flex items-center gap-2">
                    {weipuResult.detection_time_ms && (
                      <span className="text-xs text-gray-400">{weipuResult.detection_time_ms}ms</span>
                    )}
                    <button
                      onClick={() => { setFeedbackScore(weipuResult.weipu_score); setFeedbackPlatform('weipu'); setFeedbackOpen(true); }}
                      className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />反馈真实分
                    </button>
                    <button onClick={handleExport} className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" />导出报告
                    </button>
                  </div>
                </div>
                <div className="flex flex-col md:flex-row items-start gap-8">
                  <ScoreGauge score={weipuResult.weipu_score} label="预测维普AIGC分数" />
                  <div className="flex-1 space-y-3 min-w-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      weipuResult.level === 'low' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                      weipuResult.level === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                      'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    }`}>
                      {weipuResult.level === 'low' ? '低风险' : weipuResult.level === 'medium' ? '中风险' : '高风险'}
                    </span>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-2">
                        <span className="text-gray-400">句子数</span>
                        <p className="font-bold text-gray-700 dark:text-gray-300">{weipuResult.sentence_analysis.count}</p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-2">
                        <span className="text-gray-400">句长CV</span>
                        <p className={`font-bold ${weipuResult.sentence_analysis.length_cv < 0.3 ? 'text-red-500' : 'text-green-500'}`}>
                          {weipuResult.sentence_analysis.length_cv.toFixed(2)}
                        </p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-2">
                        <span className="text-gray-400">连续相似</span>
                        <p className={`font-bold ${weipuResult.sentence_analysis.consecutive_similar >= 2 ? 'text-red-500' : 'text-gray-500'}`}>
                          {weipuResult.sentence_analysis.consecutive_similar}组
                        </p>
                      </div>
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-2">
                        <span className="text-gray-400">长句比例</span>
                        <p className="font-bold text-gray-700">{(weipuResult.sentence_analysis.long_sentence_ratio * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    {weipuResult.high_risk_signals.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {weipuResult.high_risk_signals.map((s, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/20 text-red-600 border border-red-200 dark:border-red-800">{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 9-Signal breakdown */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">维普9信号检测详情</h4>
                <div className="space-y-2">
                  {weipuResult.signals.map((signal) => (
                    <div key={signal.signal_id} className={`p-2.5 rounded-lg border text-xs ${
                      signal.score > 60 ? 'border-red-200 bg-red-50 dark:bg-red-950/10 dark:border-red-800' :
                      'border-gray-100 bg-gray-50 dark:bg-gray-800/30 dark:border-gray-700'
                    }`}>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                            signal.severity === 'high' ? 'bg-red-500 text-white' :
                            signal.severity === 'medium' ? 'bg-amber-500 text-white' : 'bg-blue-400 text-white'
                          }`}>{signal.signal_id}</span>
                          <span className="font-medium text-gray-700 dark:text-gray-300">{signal.name}</span>
                          <span className={`text-xs ${
                            signal.severity === 'high' ? 'text-red-500' :
                            signal.severity === 'medium' ? 'text-amber-500' : 'text-blue-400'
                          }`}>{signal.severity === 'high' ? '高' : signal.severity === 'medium' ? '中' : '低'}</span>
                        </div>
                        <span className={`font-bold ${signal.score > 60 ? 'text-red-600' : 'text-gray-400'}`}>{signal.score.toFixed(0)}</span>
                      </div>
                      <p className="text-gray-400">{signal.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Wanfang Detection Result */}
          {activeTab === 'detect' && wanfangResult && (
            <motion.div
              key="wanfang-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-teal-500" />
                    万方对标检测结果
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      wanfangResult.level === 'significant' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      wanfangResult.level === 'suspected' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                      'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    }`}>{wanfangResult.level_label}</span>
                  </h3>
                  <div className="flex items-center gap-2">
                    {wanfangResult.detection_time_ms && <span className="text-xs text-gray-400">{wanfangResult.detection_time_ms}ms</span>}
                    <button
                      onClick={() => { setFeedbackScore(wanfangResult.wanfang_score); setFeedbackPlatform('wanfang'); setFeedbackOpen(true); }}
                      className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />反馈真实分
                    </button>
                    <button onClick={handleExport} className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" />导出报告
                    </button>
                  </div>
                </div>
                <div className="flex flex-col md:flex-row items-start gap-8">
                  <ScoreGauge score={wanfangResult.wanfang_score} label="预测万方AIGC分数" />
                  <div className="flex-1 grid grid-cols-3 gap-3 min-w-0">
                    <div className={`p-3 rounded-xl ${wanfangResult.language_features.score > 60 ? 'bg-red-50 dark:bg-red-950/20' : 'bg-gray-50 dark:bg-gray-800/30'}`}>
                      <p className="text-xs text-gray-400 mb-1">语言特征</p>
                      <p className={`text-xl font-bold ${wanfangResult.language_features.score > 60 ? 'text-red-500' : 'text-gray-700'}`}>
                        {wanfangResult.language_features.score.toFixed(0)}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">{wanfangResult.language_features.detail}</p>
                    </div>
                    <div className={`p-3 rounded-xl ${wanfangResult.content_features.score > 60 ? 'bg-red-50 dark:bg-red-950/20' : 'bg-gray-50 dark:bg-gray-800/30'}`}>
                      <p className="text-xs text-gray-400 mb-1">内容特征</p>
                      <p className={`text-xl font-bold ${wanfangResult.content_features.score > 60 ? 'text-red-500' : 'text-gray-700'}`}>
                        {wanfangResult.content_features.score.toFixed(0)}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">{wanfangResult.content_features.detail}</p>
                    </div>
                    <div className={`p-3 rounded-xl ${wanfangResult.computational_features.score > 60 ? 'bg-red-50 dark:bg-red-950/20' : 'bg-gray-50 dark:bg-gray-800/30'}`}>
                      <p className="text-xs text-gray-400 mb-1">计算特征</p>
                      <p className={`text-xl font-bold ${wanfangResult.computational_features.score > 60 ? 'text-red-500' : 'text-gray-700'}`}>
                        {wanfangResult.computational_features.score.toFixed(0)}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">{wanfangResult.computational_features.detail}</p>
                    </div>
                  </div>
                </div>
                {wanfangResult.high_risk_categories.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1">
                    {wanfangResult.high_risk_categories.map((c, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/20 text-red-600 border border-red-200 dark:border-red-800">{c}</span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Cross-Platform Comparison Result */}
          {activeTab === 'detect' && crossPlatformResult && (
            <motion.div
              key="cross-platform-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-500" />
                    三平台对比检测
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      crossPlatformResult.agreement_level === 'high' ? 'bg-green-100 text-green-700' :
                      crossPlatformResult.agreement_level === 'medium' ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>一致性: {crossPlatformResult.agreement_level === 'high' ? '高' : crossPlatformResult.agreement_level === 'medium' ? '中' : '低'}</span>
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{crossPlatformResult.total_time_ms}ms</span>
                    <button onClick={handleExport} className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors flex items-center gap-1">
                      <Download className="w-3.5 h-3.5" />导出报告
                    </button>
                  </div>
                </div>

                {/* Score comparison bar */}
                <div className="mb-6">
                  <div className="flex items-end justify-center gap-6 h-28">
                    {crossPlatformResult.platforms.map((p) => {
                      const colors: Record<string, string> = { cnki: 'bg-blue-500', weipu: 'bg-purple-500', wanfang: 'bg-teal-500' };
                      const labels: Record<string, string> = { cnki: '知网', weipu: '维普', wanfang: '万方' };
                      const height = Math.max(8, p.score);
                      return (
                        <div key={p.platform} className="flex flex-col items-center gap-1">
                          <span className={`text-sm font-bold ${p.score >= 70 ? 'text-red-500' : p.score >= 30 ? 'text-amber-500' : 'text-green-500'}`}>
                            {p.score.toFixed(0)}
                          </span>
                          <div className={`w-14 ${colors[p.platform] || 'bg-gray-400'} rounded-t-lg transition-all`}
                               style={{ height: `${height}%` }} />
                          <span className="text-xs text-gray-500 mt-1">{labels[p.platform] || p.platform_label}</span>
                          <span className={`text-xs ${
                            p.level === 'high' || p.level === 'significant' ? 'text-red-500' :
                            p.level === 'medium' || p.level === 'suspected' ? 'text-amber-500' : 'text-green-500'
                          }`}>
                            {p.level === 'high' || p.level === 'significant' ? '高风险' :
                             p.level === 'medium' || p.level === 'suspected' ? '中风险' : '低风险'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="text-center mt-3">
                    <p className="text-sm text-gray-500">
                      综合得分: <span className="font-bold text-gray-700 dark:text-gray-300">{crossPlatformResult.consensus_score.toFixed(0)}</span>
                      <span className="text-xs text-gray-400 ml-2">
                        (范围: {crossPlatformResult.score_range[0].toFixed(0)} - {crossPlatformResult.score_range[1].toFixed(0)})
                      </span>
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      最严格: <span className="text-red-500">{crossPlatformResult.strictest_platform}</span>
                      {' · '}最宽松: <span className="text-green-500">{crossPlatformResult.most_lenient_platform}</span>
                    </p>
                  </div>
                </div>

                {/* Strategy guide */}
                {crossPlatformResult.strategy_guide && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-xl border border-blue-200 dark:border-blue-800">
                    <h4 className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-2">平台差异化策略指南</h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-line leading-relaxed">
                      {crossPlatformResult.strategy_guide}
                    </p>
                  </div>
                )}
              </div>

              {/* Per-platform details */}
              {crossPlatformResult.platforms.map((p) => (
                <div key={p.platform} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    {p.platform_label} · 得分 {p.score.toFixed(0)} · {p.detection_time_ms}ms
                  </h4>
                  {p.high_risk_items.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {p.high_risk_items.map((item, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded bg-red-50 dark:bg-red-950/20 text-red-600 border border-red-200 dark:border-red-800">{item}</span>
                      ))}
                    </div>
                  )}
                  {p.suggestions.length > 0 && (
                    <ul className="space-y-1">
                      {p.suggestions.slice(0, 4).map((s, i) => (
                        <li key={i} className="text-xs text-gray-500 pl-3 border-l-2 border-gray-200 dark:border-gray-700">{s}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </motion.div>
          )}

          {/* Rewrite v2 Result */}
          {activeTab === 'rewrite' && rewriteV2Result && (
            <motion.div
              key="rewrite-v2-result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <PenLine className="w-4 h-4 text-blue-500" />
                    知网对抗改写结果
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                      {rewriteV2Result.rounds}轮改写
                    </span>
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

                {/* Score change */}
                <div className="flex items-center justify-center gap-6 mb-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-400 mb-1">改写前</p>
                    <p className="text-3xl font-bold text-red-500">{rewriteV2Result.original_score.toFixed(0)}</p>
                    <p className="text-xs text-gray-400">知网AIGC分</p>
                  </div>
                  <div className="text-2xl text-gray-300">→</div>
                  <div className="text-center">
                    <p className="text-xs text-gray-400 mb-1">改写后</p>
                    <p className="text-3xl font-bold text-green-500">{rewriteV2Result.new_score.toFixed(0)}</p>
                    <p className="text-xs text-gray-400">知网AIGC分</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-400 mb-1">降低</p>
                    <p className="text-2xl font-bold text-blue-500">
                      ↓{rewriteV2Result.score_improvement.toFixed(0)}
                    </p>
                  </div>
                </div>

                {/* Changes summary */}
                <p className="text-sm text-gray-500 mb-4 text-center">{rewriteV2Result.changes_summary}</p>

                {/* Dimension score comparison */}
                <div className="p-4 bg-gray-50 dark:bg-gray-800/30 rounded-xl">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    各维度分数变化
                  </h4>
                  <DimensionScoreCompare
                    before={rewriteV2Result.dimension_scores_before}
                    after={rewriteV2Result.dimension_scores_after}
                  />
                </div>

                {/* Triggered dimensions */}
                {rewriteV2Result.triggered_dimensions.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    <span className="text-xs text-gray-400">触发的改写维度:</span>
                    {rewriteV2Result.triggered_dimensions.map((dim, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400">
                        {dim}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Diff viewer */}
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 shadow-sm">
                <DiffViewer
                  original={text}
                  rewritten={rewriteV2Result.rewritten_text}
                  changesSummary={rewriteV2Result.changes_summary}
                  newScore={rewriteV2Result.new_score}
                />
              </div>
            </motion.div>
          )}

          {/* Rewrite result (v1) */}
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
        {!detectResult && !cnkiResult && !weipuResult && !wanfangResult && !crossPlatformResult && !compareResult && !rewriteResult && !rewriteV2Result && (
          <div className="text-center py-16 text-gray-400">
            <ScanEye className="w-12 h-12 mx-auto mb-4 opacity-40" />
            <p className="text-sm">输入文本后开始分析</p>
          </div>
        )}

        {/* Report-driven rewrite panel (精准降AI) */}
        {activeTab === 'rewrite' && text.length >= 50 && (
          <div className="mt-6">
            <ReportRewritePanel originalText={text} />
          </div>
        )}

        {/* Public accuracy dashboard */}
        <div className="mt-6">
          <AccuracyDashboard />
        </div>
      </main>

      {/* Feedback modal */}
      <FeedbackModal
        isOpen={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        ourPredictedScore={feedbackScore}
        inputText={text}
        platform={feedbackPlatform}
      />
    </div>
  );
}
