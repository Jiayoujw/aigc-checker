import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, TrendingUp, ChevronDown, ChevronRight, Target, ExternalLink } from 'lucide-react';
import { getAccuracyDashboard, getErrorDistribution } from '../services/api';
import type { AccuracyDashboardResponse, ErrorDistributionResponse } from '../types';
import { toast } from './Toast';

const PLATFORM_TABS = [
  { key: 'overview', label: '总览' },
  { key: 'cnki', label: '知网' },
  { key: 'weipu', label: '维普' },
  { key: 'wanfang', label: '万方' },
];

export default function AccuracyDashboard() {
  const [expanded, setExpanded] = useState(false);
  const [dashboard, setDashboard] = useState<AccuracyDashboardResponse | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [errorDist, setErrorDist] = useState<ErrorDistributionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchDashboard = useCallback(async () => {
    try {
      const data = await getAccuracyDashboard();
      setDashboard(data);
    } catch { /* public endpoint - ignore errors */ }
  }, []);

  useEffect(() => {
    if (expanded) fetchDashboard();
  }, [expanded, fetchDashboard]);

  const fetchErrorDist = useCallback(async (platform: string) => {
    if (platform === 'overview') { setErrorDist(null); return; }
    setLoading(true);
    try {
      const data = await getErrorDistribution(platform);
      setErrorDist(data);
    } catch {
      toast('获取误差分布失败', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  const maxErrorBucket = errorDist
    ? Math.max(...Object.values(errorDist.error_distribution), 1)
    : 1;

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-green-500" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            公开精度看板
          </span>
          <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
            实时验证
          </span>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
      </button>

      <AnimatePresence>
        {expanded && dashboard && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4 border-t border-gray-100 dark:border-gray-800">
              {/* SpeedAI comparison banner */}
              <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-950/20 dark:to-green-950/20 border border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <Target className="w-3.5 h-3.5 text-blue-500" />
                      与 SpeedAI 对标
                    </p>
                    <p className="text-2xl font-bold text-gray-800 dark:text-gray-200 mt-1">
                      {dashboard.overall.overall_mae.toFixed(1)}%
                      <span className="text-sm font-normal text-gray-500 ml-2">MAE</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">SpeedAI 声称</p>
                    <p className="text-xl font-bold text-gray-400">10.0%</p>
                  </div>
                </div>
                {dashboard.comparison_to_speedai.we_are_better !== null && (
                  <div className={`mt-2 text-xs font-medium px-3 py-1.5 rounded-lg ${
                    dashboard.comparison_to_speedai.we_are_better
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                      : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
                  }`}>
                    {dashboard.comparison_to_speedai.note}
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-2">
                  基于 {dashboard.overall.total_calibration_samples} 条真实用户校准数据 · 数据越多样本越多越精准
                </p>
              </div>

              {/* Platform tabs */}
              <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                {PLATFORM_TABS.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => { setActiveTab(tab.key); fetchErrorDist(tab.key); }}
                    className={`flex-1 py-1.5 text-xs rounded-md transition-colors ${
                      activeTab === tab.key
                        ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Platform metrics */}
              {activeTab === 'overview' ? (
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(dashboard.platforms).map(([key, p]) => (
                    <div key={key} className="p-3 bg-gray-50 dark:bg-gray-800/30 rounded-xl text-center">
                      <p className="text-xs text-gray-500 mb-1">{p.platform_label}</p>
                      <p className={`text-xl font-bold ${
                        p.mean_absolute_error <= 10 ? 'text-green-500' :
                        p.mean_absolute_error <= 15 ? 'text-amber-500' : 'text-red-500'
                      }`}>
                        {p.mean_absolute_error.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {p.total_samples} 样本 · r={p.correlation.toFixed(2)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                dashboard.platforms[activeTab] && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        ['MAE', `${dashboard.platforms[activeTab].mean_absolute_error.toFixed(1)}%`, dashboard.platforms[activeTab].mean_absolute_error <= 10 ? 'text-green-500' : 'text-amber-500'],
                        ['RMSE', `${dashboard.platforms[activeTab].rmse.toFixed(1)}%`, 'text-gray-700 dark:text-gray-300'],
                        ['相关系数', dashboard.platforms[activeTab].correlation.toFixed(2), 'text-gray-700 dark:text-gray-300'],
                        ['±10%内', `${(dashboard.platforms[activeTab].within_10_percent_rate * 100).toFixed(0)}%`, 'text-gray-700 dark:text-gray-300'],
                      ].map(([label, value, color]) => (
                        <div key={label as string} className="p-2 bg-gray-50 dark:bg-gray-800/30 rounded-lg text-center">
                          <p className="text-xs text-gray-400">{label}</p>
                          <p className={`text-sm font-bold ${color}`}>{value}</p>
                        </div>
                      ))}
                    </div>

                    {dashboard.platforms[activeTab].recent_mae_30d > 0 && (
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        近30天MAE: {dashboard.platforms[activeTab].recent_mae_30d.toFixed(1)}%
                      </p>
                    )}

                    {/* Error distribution chart */}
                    {loading ? (
                      <div className="flex items-center justify-center py-8">
                        <span className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                      </div>
                    ) : errorDist && errorDist.total_samples > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500">误差分布 (最近{errorDist.total_samples}条)</p>
                        {Object.entries(errorDist.error_distribution).map(([bucket, count]) => {
                          const labels: Record<string, string> = {
                            within_5: '0-5%', within_5_to_10: '5-10%', within_10_to_15: '10-15%',
                            within_15_to_20: '15-20%', over_20: '>20%',
                          };
                          const pct = (count / errorDist.total_samples) * 100;
                          const barColor = bucket === 'within_5' ? 'bg-green-500' :
                            bucket === 'within_5_to_10' ? 'bg-blue-400' :
                            bucket === 'within_10_to_15' ? 'bg-amber-400' :
                            bucket === 'within_15_to_20' ? 'bg-orange-400' : 'bg-red-400';
                          return (
                            <div key={bucket} className="flex items-center gap-2 text-xs">
                              <span className="w-12 text-gray-500 text-right">{labels[bucket] || bucket}</span>
                              <div className="flex-1 h-4 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${barColor} transition-all`}
                                     style={{ width: `${Math.max(pct, 2)}%` }} />
                              </div>
                              <span className="w-14 text-gray-600 dark:text-gray-400">
                                {count} ({pct.toFixed(0)}%)
                              </span>
                            </div>
                          );
                        })}

                        {/* Trend */}
                        {errorDist.trend.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                              <TrendingUp className="w-3 h-3" />
                              周趋势
                            </p>
                            <div className="flex items-end gap-1 h-16">
                              {errorDist.trend.map((t) => {
                                const maxMae = Math.max(...errorDist.trend.map(x => x.mae), 1);
                                const height = (t.mae / maxMae) * 100;
                                return (
                                  <div key={t.week} className="flex-1 flex flex-col items-center gap-0.5">
                                    <span className="text-xs text-gray-400">{t.mae.toFixed(1)}</span>
                                    <div
                                      className="w-full bg-blue-400 rounded-t"
                                      style={{ height: `${Math.max(height, 8)}%` }}
                                      title={`${t.week}: MAE ${t.mae}% (${t.samples}样本)`}
                                    />
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 text-center py-4">暂无数据，提交反馈后可见</p>
                    )}
                  </div>
                )
              )}

              <p className="text-xs text-gray-400 flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                数据公开透明 · 每一条用户反馈都在提升精度
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
