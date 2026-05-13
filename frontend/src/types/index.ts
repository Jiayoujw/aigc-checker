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
