export interface DetectRequest {
  text: string;
  provider: 'deepseek' | 'openai' | 'auto';
  mode: 'general' | 'academic' | 'resume' | 'social_media';
}

export interface DetectResponse {
  score: number;
  level: 'low' | 'medium' | 'high';
  suspicious_segments: SuspiciousSegment[];
  analysis: string;
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

export interface PlagiarismRequest {
  text: string;
}

export interface PlagiarismResponse {
  similarity_score: number;
  similar_sources: SimilarSource[];
  details: string;
}

export interface SimilarSource {
  text: string;
  reason: string;
  possible_source_type: string;
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
  type: 'detect' | 'plagiarism' | 'rewrite';
  input_text: string;
  result_json: string;
  created_at: string;
}
