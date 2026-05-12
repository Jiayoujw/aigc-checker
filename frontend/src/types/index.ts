export interface DetectRequest {
  text: string;
  provider: 'deepseek' | 'openai' | 'auto';
}

export interface DetectResponse {
  score: number;
  level: 'low' | 'medium' | 'high';
  suspicious_segments: SuspiciousSegment[];
  analysis: string;
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
}

export interface RewriteResponse {
  rewritten_text: string;
  changes_summary: string;
  new_aigc_score: number;
}

export type TabType = 'detect' | 'rewrite' | 'plagiarism';
