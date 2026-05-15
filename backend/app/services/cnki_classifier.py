"""
Dedicated AIGC classifier combining CNKI feature vectors with ML.

This provides:
  1. A lightweight RandomForest/XGBoost classifier trained on CNKI 8-dim features
     (no GPU needed, fast inference, easy to deploy on Render free tier)
  2. A deep learning path (Qwen3-8B + LoRA) for higher accuracy when GPU available

The lightweight model uses CNKI feature vectors as input and predicts
the probability that CNKI would flag the text as AI-generated.

Training data flow:
  HC3-Chinese / C-ReD → extract CNKI features → train classifier → predict CNKI score
"""

import json
import pickle
import os
from dataclasses import dataclass
from typing import Literal

from .cnki_feature_scanner import scan_cnki_features, CNKIFeatureReport


# ---------------------------------------------------------------------------
# Feature vector extraction
# ---------------------------------------------------------------------------
def extract_feature_vector(report: CNKIFeatureReport) -> list[float]:
    """Convert CNKI feature report to a fixed-size feature vector for ML."""
    return [
        # D1: Sentence structure
        report.sentence_structure.score,
        report.sentence_structure.cv,
        report.sentence_structure.mean_len,
        report.sentence_structure.std_len,
        1.0 if report.sentence_structure.distribution_type == "unimodal" else 0.0,
        1.0 if report.sentence_structure.distribution_type == "bimodal" else 0.0,
        1.0 if report.sentence_structure.distribution_type == "multimodal" else 0.0,
        # D2: Paragraph similarity
        report.paragraph_similarity.score,
        report.paragraph_similarity.mean_similarity,
        float(report.paragraph_similarity.paragraph_count),
        # D3: Information density
        report.information_density.score,
        report.information_density.mean_density,
        report.information_density.std_density,
        # D4: Connectors
        report.connectors.score,
        report.connectors.per_1000_chars,
        report.connectors.uniformity_score,
        float(report.connectors.total_connectors),
        # D5: Terminology
        report.terminology.score,
        report.terminology.term_density,
        report.terminology.term_variation,
        # D6: Citations
        report.citations.score,
        float(report.citations.citation_count),
        1.0 if report.citations.has_specific_refs else 0.0,
        # D7: Data specificity
        report.data_specificity.score,
        report.data_specificity.number_density,
        1.0 if report.data_specificity.has_specific_data else 0.0,
        # D8: Logical coherence
        report.logical_coherence.score,
        report.logical_coherence.transition_quality,
        float(report.logical_coherence.paragraph_transitions),
    ]


FEATURE_NAMES = [
    "sent_score", "sent_cv", "sent_mean_len", "sent_std_len",
    "sent_unimodal", "sent_bimodal", "sent_multimodal",
    "para_score", "para_mean_sim", "para_count",
    "density_score", "density_mean", "density_std",
    "connector_score", "connector_per_1000", "connector_uniformity", "connector_total",
    "term_score", "term_density", "term_variation",
    "citation_score", "citation_count", "citation_has_specific",
    "data_score", "data_number_density", "data_has_specific",
    "logical_score", "logical_transition_quality", "logical_transition_count",
]


# ---------------------------------------------------------------------------
# Rule-based fallback (when no trained model available)
# ---------------------------------------------------------------------------
def rule_based_predict(report: CNKIFeatureReport) -> dict:
    """
    Rule-based prediction using CNKI feature scores.
    This is a deterministic fallback that works without training data.
    """
    scores = {
        "sentence_structure": report.sentence_structure.score,
        "paragraph_similarity": report.paragraph_similarity.score,
        "information_density": report.information_density.score,
        "connectors": report.connectors.score,
        "terminology": report.terminology.score,
        "citations": report.citations.score,
        "data_specificity": report.data_specificity.score,
        "logical_coherence": report.logical_coherence.score,
    }

    # High-trigger: 3+ dimensions > 70
    high_count = sum(1 for s in scores.values() if s > 70)
    mid_count = sum(1 for s in scores.values() if s > 50)

    if high_count >= 4:
        cnki_score = 85.0
        confidence = 0.85
    elif high_count >= 2:
        cnki_score = 70.0
        confidence = 0.75
    elif mid_count >= 3:
        cnki_score = 55.0
        confidence = 0.65
    elif mid_count >= 1:
        cnki_score = 35.0
        confidence = 0.60
    else:
        cnki_score = 15.0
        confidence = 0.70

    level = "high" if cnki_score >= 70 else ("medium" if cnki_score >= 30 else "low")

    return {
        "cnki_score": cnki_score,
        "level": level,
        "confidence": confidence,
        "high_risk_count": high_count,
        "mid_risk_count": mid_count,
        "dimension_scores": scores,
        "method": "rule_based",
    }


# ---------------------------------------------------------------------------
# ML-based prediction (when model is available)
# ---------------------------------------------------------------------------
_model = None  # lazy-loaded singleton


def _load_model():
    global _model
    if _model is not None:
        return _model

    model_path = os.path.join(os.path.dirname(__file__), "..", "cnki_model.pkl")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            _model = pickle.load(f)
        return _model
    return None


def ml_based_predict(report: CNKIFeatureReport) -> dict:
    """ML-based prediction using trained classifier."""
    model = _load_model()
    if model is None:
        return None  # fall back to rule-based

    features = extract_feature_vector(report)
    proba = model.predict_proba([features])[0]
    # Assuming binary: [P(human), P(AI)]
    if len(proba) >= 2:
        cnki_score = round(proba[1] * 100, 1)
    else:
        cnki_score = round(proba[0] * 100, 1)

    level = "high" if cnki_score >= 70 else ("medium" if cnki_score >= 30 else "low")

    return {
        "cnki_score": cnki_score,
        "level": level,
        "confidence": round(float(max(proba)), 3),
        "method": "ml_model",
    }


# ---------------------------------------------------------------------------
# Unified prediction API
# ---------------------------------------------------------------------------
def predict_cnki_score(
    text: str,
    mode: str = "general",
    discipline: str | None = None,
) -> dict:
    """
    Unified CNKI score prediction combining CNKI feature scan + ML/rule classifier.

    Returns a prediction of what CNKI's AIGC detection score would be for this text.
    """
    report = scan_cnki_features(text, mode=mode, discipline=discipline)

    # Try ML first, fall back to rule-based
    result = ml_based_predict(report)
    if result is None:
        result = rule_based_predict(report)

    # Attach detailed dimension breakdown
    result["dimension_breakdown"] = {
        "sentence_structure": {
            "score": report.sentence_structure.score,
            "detail": report.sentence_structure.detail,
        },
        "paragraph_similarity": {
            "score": report.paragraph_similarity.score,
            "detail": report.paragraph_similarity.detail,
        },
        "information_density": {
            "score": report.information_density.score,
            "detail": report.information_density.detail,
        },
        "connectors": {
            "score": report.connectors.score,
            "detail": report.connectors.detail,
        },
        "terminology": {
            "score": report.terminology.score,
            "detail": report.terminology.detail,
        },
        "citations": {
            "score": report.citations.score,
            "detail": report.citations.detail,
        },
        "data_specificity": {
            "score": report.data_specificity.score,
            "detail": report.data_specificity.detail,
        },
        "logical_coherence": {
            "score": report.logical_coherence.score,
            "detail": report.logical_coherence.detail,
        },
    }
    result["rewrite_suggestions"] = report.rewrite_suggestions
    result["high_risk_dimensions"] = report.high_risk_dimensions

    return result
