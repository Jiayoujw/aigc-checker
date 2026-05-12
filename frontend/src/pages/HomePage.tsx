import { useState, useCallback } from 'react';
import type {
  DetectResponse,
  PlagiarismResponse,
  RewriteResponse,
} from '../types';
import { detectAigc, checkPlagiarism, rewriteText } from '../services/api';
import Navbar from '../components/Navbar';
import TextInput from '../components/TextInput';
import ResultCard from '../components/ResultCard';
import ScoreGauge from '../components/ScoreGauge';
import HighlightText from '../components/HighlightText';
import DiffViewer from '../components/DiffViewer';

export default function HomePage() {
  const [text, setText] = useState('');
  const [activeTab, setActiveTab] = useState<
    'detect' | 'rewrite' | 'plagiarism' | null
  >(null);

  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null);
  const [rewriteResult, setRewriteResult] =
    useState<RewriteResponse | null>(null);
  const [plagiarismResult, setPlagiarismResult] =
    useState<PlagiarismResponse | null>(null);

  const [detectLoading, setDetectLoading] = useState(false);
  const [rewriteLoading, setRewriteLoading] = useState(false);
  const [plagiarismLoading, setPlagiarismLoading] = useState(false);

  const [detectError, setDetectError] = useState<string | null>(null);
  const [rewriteError, setRewriteError] = useState<string | null>(null);
  const [plagiarismError, setPlagiarismError] = useState<string | null>(null);

  const canSubmit = text.length >= 50;

  const handleDetect = useCallback(async () => {
    if (!canSubmit) return;
    setActiveTab('detect');
    setDetectLoading(true);
    setDetectError(null);
    try {
      const res = await detectAigc({ text, provider: 'auto' });
      setDetectResult(res);
    } catch (e) {
      setDetectError(e instanceof Error ? e.message : '检测失败');
    } finally {
      setDetectLoading(false);
    }
  }, [text, canSubmit]);

  const handlePlagiarism = useCallback(async () => {
    if (!canSubmit) return;
    setActiveTab('plagiarism');
    setPlagiarismLoading(true);
    setPlagiarismError(null);
    try {
      const res = await checkPlagiarism({ text });
      setPlagiarismResult(res);
    } catch (e) {
      setPlagiarismError(e instanceof Error ? e.message : '查重失败');
    } finally {
      setPlagiarismLoading(false);
    }
  }, [text, canSubmit]);

  const handleRewrite = useCallback(async () => {
    if (!canSubmit) return;
    setActiveTab('rewrite');
    setRewriteLoading(true);
    setRewriteError(null);
    try {
      const res = await rewriteText({ text, provider: 'auto' });
      setRewriteResult(res);
    } catch (e) {
      setRewriteError(e instanceof Error ? e.message : '改写失败');
    } finally {
      setRewriteLoading(false);
    }
  }, [text, canSubmit]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Input Section */}
        <div className="mb-6">
          <TextInput value={text} onChange={setText} />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-8">
          <button
            onClick={handleDetect}
            disabled={!canSubmit || detectLoading}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all
                       bg-blue-500 text-white hover:bg-blue-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       active:scale-[0.98]"
          >
            {detectLoading ? '检测中...' : '🔍 AIGC检测'}
          </button>
          <button
            onClick={handlePlagiarism}
            disabled={!canSubmit || plagiarismLoading}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all
                       bg-purple-500 text-white hover:bg-purple-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       active:scale-[0.98]"
          >
            {plagiarismLoading ? '检测中...' : '📑 查重检测'}
          </button>
          <button
            onClick={handleRewrite}
            disabled={!canSubmit || rewriteLoading}
            className="flex-1 py-3 rounded-lg font-medium text-sm transition-all
                       bg-emerald-500 text-white hover:bg-emerald-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       active:scale-[0.98]"
          >
            {rewriteLoading ? '改写中...' : '✏️ 一键降AIGC'}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {/* AIGC Detection Result */}
          {activeTab === 'detect' && (
            <ResultCard
              title="AIGC检测结果"
              loading={detectLoading}
              error={detectError}
            >
              {detectResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-6">
                    <ScoreGauge score={detectResult.score} label="AI生成概率" />
                    <p className="text-sm text-gray-600 leading-relaxed flex-1">
                      {detectResult.analysis}
                    </p>
                  </div>
                  <HighlightText segments={detectResult.suspicious_segments} />
                </div>
              )}
            </ResultCard>
          )}

          {/* Plagiarism Result */}
          {activeTab === 'plagiarism' && (
            <ResultCard
              title="查重检测结果"
              loading={plagiarismLoading}
              error={plagiarismError}
            >
              {plagiarismResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-6">
                    <ScoreGauge
                      score={plagiarismResult.similarity_score}
                      label="重复率"
                    />
                    <p className="text-sm text-gray-600 leading-relaxed flex-1">
                      {plagiarismResult.details}
                    </p>
                  </div>
                  {plagiarismResult.similar_sources.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs text-gray-500 font-medium">
                        相似来源：
                      </p>
                      {plagiarismResult.similar_sources.map((src, i) => (
                        <div
                          key={i}
                          className="bg-orange-50 border border-orange-200 rounded-lg p-3"
                        >
                          <p className="text-sm text-gray-800">{src.text}</p>
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
                  )}
                  {plagiarismResult.similar_sources.length === 0 && (
                    <p className="text-sm text-green-600 bg-green-50 rounded-lg p-3">
                      未发现明显重复内容
                    </p>
                  )}
                </div>
              )}
            </ResultCard>
          )}

          {/* Rewrite Result */}
          {activeTab === 'rewrite' && (
            <ResultCard
              title="降AIGC改写结果"
              loading={rewriteLoading}
              error={rewriteError}
            >
              {rewriteResult && (
                <DiffViewer
                  original={text}
                  rewritten={rewriteResult.rewritten_text}
                  changesSummary={rewriteResult.changes_summary}
                  newScore={rewriteResult.new_aigc_score}
                />
              )}
            </ResultCard>
          )}
        </div>

        {/* Empty state */}
        {!activeTab && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-4">&#x1F4DD;</p>
            <p className="text-sm">
              粘贴文本后点击上方按钮开始分析
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
