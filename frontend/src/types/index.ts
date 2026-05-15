export interface DetectRequest {
  text: string;
  provider: 'deepseek' | 'openai' | 'auto';
  mode: 'general' | 'academic' | 'resume' | 'social_media';
}

export interface StatisticalAnalysis {
  score: number;
  perplexity: number;
  burstiness: number;
  template_hits: number;
  lexical_diversity: number;
  sentence_count: number;
  avg_sentence_len: number;
  sentence_len_std: number;
  details: string[];
}

export interface FusedResult {
  combined_score: number;
  llm_score: number;
  statistical_score: number;
  confidence: 'high' | 'medium' | 'low';
  level: 'low' | 'medium' | 'high';
}

export interface ParagraphResult {
  index: number;
  text: string;
  char_count: number;
  stat_score: number;
  llm_score: number | null;
  fused_score: number;
  level: 'low' | 'medium' | 'high';
  stat_details: string[];
}

export interface DetectResponse {
  score: number;
  level: 'low' | 'medium' | 'high';
  suspicious_segments: SuspiciousSegment[];
  analysis: string;
  // Multi-dimensional analysis (short text)
  statistical_analysis?: StatisticalAnalysis;
  fused_result?: FusedResult;
  // Paragraph-level (long text)
  confidence?: 'high' | 'medium' | 'low';
  mixed_content?: boolean;
  paragraph_count?: number;
  score_distribution?: { low: number; medium: number; high: number };
  paragraphs?: ParagraphResult[];
  detection_time_ms?: number;
  provider?: string;
  mode?: string;
}

export interface CompareResponse {
  deepseek: DetectResponse;
  openai: DetectResponse;
  consensus: {
    level: string;
    avg_score: number;
    diff?: number;
    agreement?: string;
  };
}

export interface SuspiciousSegment {
  text: string;
  score: number;
  reason: string;
}

export interface RewriteRequest {
  text: string;
  provider: 'deepseek' | 'openai' | 'auto';
  intensity: 'light' | 'medium' | 'deep';
  preserve_terms: boolean;
}

export interface RewriteResponse {
  rewritten_text: string;
  changes_summary: string;
  new_aigc_score: number;
}

export interface HistoryRecord {
  id: string;
  type: 'detect' | 'rewrite';
  input_text: string;
  result_json: string;
  created_at: string;
}

// ---- CNKI-specific types ----

export interface CNKIDetectRequest {
  text: string;
  mode: 'general' | 'academic' | 'resume' | 'social_media';
  discipline?: string;
  provider?: 'deepseek' | 'openai' | 'auto';
}

export interface DimensionScore {
  score: number;
  detail: string;
}

export interface DimensionBreakdown {
  sentence_structure: DimensionScore;
  paragraph_similarity: DimensionScore;
  information_density: DimensionScore;
  connectors: DimensionScore;
  terminology: DimensionScore;
  citations: DimensionScore;
  data_specificity: DimensionScore;
  logical_coherence: DimensionScore;
}

export interface CNKIDetectResponse {
  cnki_score: number;
  level: 'low' | 'medium' | 'high';
  confidence: number;
  method: string;
  dimension_breakdown: DimensionBreakdown;
  high_risk_dimensions: string[];
  rewrite_suggestions: string[];
  detection_time_ms?: number;
}

export interface InfoDiffResponse {
  info_diff_score: number;
  level: 'low' | 'medium' | 'high';
  confidence: 'high' | 'medium' | 'low';
  info_diff: number;
  original_info: Record<string, number>;
  variant_infos: Record<string, number>[];
  mean_variant_composite: number;
  detail: string;
  detection_time_ms?: number;
}

export interface RewriteV2Request {
  text: string;
  provider: 'deepseek' | 'openai' | 'auto';
  intensity: 'light' | 'medium' | 'deep';
  mode: string;
  target_score: number;
  max_rounds: number;
}

export interface RewriteV2Response {
  rewritten_text: string;
  original_score: number;
  new_score: number;
  rounds: number;
  score_improvement: number;
  changes_summary: string;
  triggered_dimensions: string[];
  dimension_scores_before: Record<string, number>;
  dimension_scores_after: Record<string, number>;
}

// ---- Weipu / Wanfang / Cross-Platform types ----

export interface WeipuSignal {
  signal_id: number;
  name: string;
  severity: 'high' | 'medium' | 'low';
  score: number;
  detail: string;
}

export interface WeipuDetectResponse {
  weipu_score: number;
  level: 'low' | 'medium' | 'high';
  signals: WeipuSignal[];
  sentence_analysis: {
    count: number;
    mean_len: number;
    length_cv: number;
    consecutive_similar: number;
    long_sentence_ratio: number;
    adj_diff_cv: number;
    detail: string;
  };
  high_risk_signals: string[];
  rewrite_suggestions: string[];
  detection_time_ms?: number;
}

export interface WanfangDetectResponse {
  wanfang_score: number;
  level: 'excluded' | 'suspected' | 'significant';
  level_label: string;
  language_features: {
    connector_density: number;
    sentence_pattern_variety: number;
    expression_flexibility: number;
    score: number;
    detail: string;
  };
  content_features: {
    innovation_score: number;
    logic_depth_score: number;
    subjectivity_score: number;
    score: number;
    detail: string;
  };
  computational_features: {
    char_optimality: number;
    collocation_perfection: number;
    perplexity_score: number;
    score: number;
    detail: string;
  };
  high_risk_categories: string[];
  rewrite_suggestions: string[];
  detection_time_ms?: number;
}

export interface PlatformInfo {
  platform: 'cnki' | 'weipu' | 'wanfang';
  platform_label: string;
  score: number;
  level: string;
  high_risk_items: string[];
  suggestions: string[];
  detection_time_ms: number;
}

export interface CrossPlatformResponse {
  platforms: PlatformInfo[];
  consensus_score: number;
  score_range: [number, number];
  agreement_level: 'high' | 'medium' | 'low';
  strictest_platform: string;
  most_lenient_platform: string;
  unified_level: string;
  unified_suggestions: string[];
  strategy_guide: string;
  total_time_ms: number;
}

// ---- Credit/Quota types ----

export interface CreditStats {
  daily_detect_used: number;
  daily_detect_total: number;
  daily_rewrite_used: number;
  daily_rewrite_total: number;
  purchased_credits: number;
  total_detections: number;
  total_rewrites: number;
  registration_bonus_claimed: boolean;
}

export interface DetectQuota {
  can_detect: boolean;
  daily_free_remaining: number;
  daily_free_total: number;
  purchased_credits: number;
}

export interface RewriteQuota {
  can_rewrite: boolean;
  daily_free_remaining: number;
  daily_free_total: number;
  purchased_credits: number;
}

export interface QuotaResponse {
  detect: DetectQuota;
  rewrite: RewriteQuota;
}

// ---- Calibration / Feedback types ----

export interface FeedbackRequest {
  platform: 'cnki' | 'weipu' | 'wanfang';
  our_predicted_score: number;
  real_score: number;
  input_text: string;
  mode: string;
}

export interface FeedbackResponse {
  success: boolean;
  credits_earned: number;
  prediction_error: number;
  total_samples: number;
  message: string;
}

export interface CalibrationStats {
  total_samples: number;
  platforms: Record<string, {
    total_samples: number;
    mae: number;
    rmse: number;
    correlation: number;
  }>;
}

// ---- Accuracy Dashboard types ----

export interface AccuracyPlatformInfo {
  platform: string;
  platform_label: string;
  total_samples: number;
  mean_absolute_error: number;
  rmse: number;
  correlation: number;
  within_10_percent_rate: number;
  recent_mae_30d: number;
  last_calibrated_at: string | null;
  updated_at: string | null;
}

export interface AccuracyDashboardResponse {
  platforms: Record<string, AccuracyPlatformInfo>;
  overall: {
    total_calibration_samples: number;
    overall_mae: number;
  };
  comparison_to_speedai: {
    speedai_claimed_mae: number;
    our_mae: number;
    we_are_better: boolean | null;
    note: string;
  };
}

export interface ErrorDistributionResponse {
  platform: string;
  platform_label: string;
  total_samples: number;
  error_distribution: {
    within_5: number;
    within_5_to_10: number;
    within_10_to_15: number;
    within_15_to_20: number;
    over_20: number;
  };
  trend: Array<{ week: string; mae: number; samples: number }>;
}

// ---- Report Parse / Rewrite types ----

export interface ReportParseRequest {
  report_text: string;
  platform_hint: 'auto' | 'cnki' | 'weipu' | 'wanfang';
}

export interface FlaggedSectionInfo {
  text: string;
  score: number;
  risk_level: string;
}

export interface ReportParseResponse {
  platform: string;
  overall_score: number | null;
  overall_level: string | null;
  flagged_sections: FlaggedSectionInfo[];
  flagged_count: number;
  parse_confidence: number;
}

export interface ReportRewriteRequest {
  original_text: string;
  report_text: string;
  provider: string;
  intensity: 'light' | 'medium' | 'deep';
  platform_hint: string;
}

export interface SectionRewriteInfo {
  original_text: string;
  rewritten_text: string;
  original_score: number;
  new_score: number;
  improvement: number;
}

export interface ReportRewriteResponse {
  rewritten_full_text: string;
  sections_rewritten: number;
  sections_preserved: number;
  section_results: SectionRewriteInfo[];
  original_overall_score: number | null;
  estimated_new_score: number;
  changes_summary: string;
}
