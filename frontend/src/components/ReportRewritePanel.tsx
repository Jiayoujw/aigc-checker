import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileSearch, PenLine, ChevronDown, ChevronRight, Target } from 'lucide-react';
import { parseReport, rewriteFromReport } from '../services/api';
import type { ReportParseResponse, ReportRewriteResponse } from '../types';
import { toast } from './Toast';
import ScoreGauge from './ScoreGauge';

interface Props {
  originalText: string;
}

export default function ReportRewritePanel({ originalText }: Props) {
  const [reportText, setReportText] = useState('');
  const [platformHint, setPlatformHint] = useState<'auto' | 'cnki' | 'weipu' | 'wanfang'>('auto');
  const [intensity, setIntensity] = useState<'light' | 'medium' | 'deep'>('medium');
  const [expanded, setExpanded] = useState(false);

  const [parseLoading, setParseLoading] = useState(false);
  const [rewriteLoading, setRewriteLoading] = useState(false);
  const [parseResult, setParseResult] = useState<ReportParseResponse | null>(null);
  const [rewriteResult, setRewriteResult] = useState<ReportRewriteResponse | null>(null);

  const canParse = reportText.length >= 50;
  const canRewrite = canParse && originalText.length >= 50;

  const handleParse = async () => {
    if (!canParse) return;
    setParseLoading(true);
    setParseResult(null);
    try {
      const res = await parseReport({ report_text: reportText, platform_hint: platformHint });
      setParseResult(res);
    } catch (e) {
      toast(e instanceof Error ? e.message : '报告解析失败', 'error');
    } finally {
      setParseLoading(false);
    }
  };

  const handleRewrite = async () => {
    if (!canRewrite) return;
    setRewriteLoading(true);
    setRewriteResult(null);
    try {
      const res = await rewriteFromReport({
        original_text: originalText,
        report_text: reportText,
        provider: 'auto',
        intensity,
        platform_hint: platformHint,
      });
      setRewriteResult(res);
      toast('精准降AI改写完成', 'success');
    } catch (e) {
      toast(e instanceof Error ? e.message : '报告改写失败', 'error');
    } finally {
      setRewriteLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-purple-500" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            精准降AI
          </span>
          <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
            SpeedAI 对标
          </span>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4 border-t border-gray-100 dark:border-gray-800">
              <p className="text-xs text-gray-500 pt-4">
                上传官方检测报告（知网/维普/万方），精准定位被标记段落，仅改写高风险部分，保留其余原文。比全文改写更高效、更安全。
              </p>

              {/* Report text input */}
              <div>
                <label className="text-xs text-gray-500 mb-1.5 block">官方检测报告文本</label>
                <textarea
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  placeholder="粘贴知网/维普/万方检测报告全文..."
                  rows={5}
                  className="w-full px-3 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-700
                             bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                             focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none resize-none"
                />
              </div>

              {/* Options */}
              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={platformHint}
                  onChange={(e) => setPlatformHint(e.target.value as typeof platformHint)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700
                             bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300"
                >
                  <option value="auto">自动识别平台</option>
                  <option value="cnki">知网 CNKI</option>
                  <option value="weipu">维普 Weipu</option>
                  <option value="wanfang">万方 Wanfang</option>
                </select>

                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-gray-500">改写强度:</span>
                  {(['light', 'medium', 'deep'] as const).map((l) => (
                    <button
                      key={l}
                      onClick={() => setIntensity(l)}
                      className={`px-2 py-1 text-xs rounded transition-colors ${
                        intensity === l
                          ? 'bg-purple-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {l === 'light' ? '轻度' : l === 'medium' ? '中度' : '深度'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handleParse}
                  disabled={!canParse || parseLoading}
                  className="flex-1 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600
                             text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800
                             disabled:opacity-50 disabled:cursor-not-allowed transition-colors
                             flex items-center justify-center gap-2"
                >
                  {parseLoading ? (
                    <span className="w-4 h-4 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin" />
                  ) : (
                    <FileSearch className="w-4 h-4" />
                  )}
                  解析报告
                </button>
                <button
                  onClick={handleRewrite}
                  disabled={!canRewrite || rewriteLoading}
                  className="flex-1 py-2.5 text-sm rounded-lg bg-purple-500 text-white
                             hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed
                             transition-colors flex items-center justify-center gap-2"
                >
                  {rewriteLoading ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <PenLine className="w-4 h-4" />
                  )}
                  精准改写
                </button>
              </div>

              {/* Parse result */}
              {parseResult && (
                <div className="p-4 bg-gray-50 dark:bg-gray-800/30 rounded-xl">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    报告解析结果
                  </h4>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="text-center">
                      <p className="text-xs text-gray-400">平台</p>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{parseResult.platform}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-400">综合分数</p>
                      <p className="text-sm font-bold text-red-500">{parseResult.overall_score?.toFixed(0) ?? '?'}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-400">标记段落</p>
                      <p className="text-sm font-bold text-amber-500">{parseResult.flagged_count}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-400">置信度</p>
                      <p className="text-sm font-medium text-gray-600">{(parseResult.parse_confidence * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                  {parseResult.flagged_sections.length > 0 && (
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {parseResult.flagged_sections.slice(0, 5).map((s, i) => (
                        <div key={i} className="text-xs text-gray-500 flex items-start gap-2">
                          <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs text-white flex-shrink-0 ${
                            s.risk_level === 'high' ? 'bg-red-500' : s.risk_level === 'medium' ? 'bg-amber-500' : 'bg-blue-400'
                          }`}>{i + 1}</span>
                          <span className="leading-relaxed">{s.text.slice(0, 120)}{s.text.length > 120 ? '...' : ''}</span>
                          <span className="font-medium flex-shrink-0">{s.score.toFixed(0)}分</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Rewrite result */}
              {rewriteResult && (
                <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-xl border border-purple-200 dark:border-purple-800">
                  <h4 className="text-xs font-semibold text-purple-700 dark:text-purple-400 mb-3">
                    精准改写完成
                  </h4>
                  <div className="flex items-center gap-6 mb-4">
                    <div className="text-center">
                      <p className="text-xs text-gray-500">改写段落</p>
                      <p className="text-xl font-bold text-purple-600">{rewriteResult.sections_rewritten}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">保留段落</p>
                      <p className="text-xl font-bold text-green-600">{rewriteResult.sections_preserved}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">预计新分</p>
                      <ScoreGauge score={rewriteResult.estimated_new_score} label="" size="sm" />
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{rewriteResult.changes_summary}</p>

                  {/* Section results */}
                  <div className="mt-3 space-y-2 max-h-60 overflow-y-auto">
                    {rewriteResult.section_results.map((sr, i) => (
                      <div key={i} className="p-2.5 bg-white dark:bg-gray-900/50 rounded-lg text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-400">段落 {i + 1}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-red-400">{sr.original_score} →</span>
                            <span className="text-green-500 font-medium">{sr.new_score}</span>
                            <span className="text-green-500">↓{sr.improvement}</span>
                          </div>
                        </div>
                        <p className="text-gray-500 truncate">{sr.rewritten_text.slice(0, 150)}...</p>
                      </div>
                    ))}
                  </div>

                  {/* Full rewritten text */}
                  <details className="mt-3">
                    <summary className="text-xs text-purple-500 cursor-pointer hover:text-purple-600">
                      查看完整改写文本
                    </summary>
                    <div className="mt-2 p-3 bg-white dark:bg-gray-900 rounded-lg text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap max-h-80 overflow-y-auto">
                      {rewriteResult.rewritten_full_text}
                    </div>
                  </details>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
