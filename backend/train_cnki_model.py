"""
Train a CNKI AIGC detection classifier using open-source datasets.

Datasets used:
  - HC3-Chinese (huggingface: Hello-SimpleAI/HC3-Chinese)
  - The model uses our CNKI 8-dim feature extraction + XGBoost classifier

Usage:
  python train_cnki_model.py --download    # Download datasets
  python train_cnki_model.py --train       # Train model
  python train_cnki_model.py --evaluate    # Evaluate on test set

Output:
  app/cnki_model.pkl  — Trained XGBoost model for production inference
"""

import argparse
import json
import os
import pickle
import sys

import numpy as np

# Add parent to path so we can import app services
sys.path.insert(0, os.path.dirname(__file__))

from app.services.cnki_feature_scanner import scan_cnki_features
from app.services.cnki_classifier import extract_feature_vector, FEATURE_NAMES


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------
def load_hc3_chinese(data_dir: str = "./data/hc3") -> tuple[np.ndarray, np.ndarray]:
    """
    Load HC3-Chinese dataset.
    Returns (features, labels) where label=1 means AI-generated.
    """
    features = []
    labels = []

    # Try loading from HuggingFace datasets first
    try:
        from datasets import load_dataset
        print("Loading HC3-Chinese from HuggingFace...")
        dataset = load_dataset("Hello-SimpleAI/HC3-Chinese", split="train")
        print(f"Loaded {len(dataset)} samples")
    except Exception as e:
        print(f"HuggingFace load failed: {e}")
        print("Trying local files...")
        return _load_local_hc3(data_dir)

    for item in dataset:
        try:
            # Human answer
            human_text = item.get("human_answers", [""])[0] if item.get("human_answers") else ""
            if human_text and len(human_text) >= 50:
                report = scan_cnki_features(human_text)
                features.append(extract_feature_vector(report))
                labels.append(0)  # human

            # AI answer
            ai_text = item.get("chatgpt_answers", [""])[0] if item.get("chatgpt_answers") else ""
            if ai_text and len(ai_text) >= 50:
                report = scan_cnki_features(ai_text)
                features.append(extract_feature_vector(report))
                labels.append(1)  # AI
        except Exception:
            continue

    print(f"Extracted features for {len(features)} samples "
          f"({labels.count(1)} AI, {labels.count(0)} human)")
    return np.array(features), np.array(labels)


def _load_local_hc3(data_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """Fallback: load HC3 from local JSONL files."""
    features = []
    labels = []

    for filename in ["hc3_chinese_train.jsonl", "hc3_chinese.jsonl"]:
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            continue
        print(f"Loading {path}...")
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    for answer in item.get("human_answers", []):
                        if len(answer) >= 50:
                            report = scan_cnki_features(answer)
                            features.append(extract_feature_vector(report))
                            labels.append(0)
                    for answer in item.get("chatgpt_answers", []):
                        if len(answer) >= 50:
                            report = scan_cnki_features(answer)
                            features.append(extract_feature_vector(report))
                            labels.append(1)
                except (json.JSONDecodeError, KeyError):
                    continue
        break

    print(f"Local: {len(features)} samples ({labels.count(1)} AI, {labels.count(0)} human)")
    return np.array(features), np.array(labels)


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------
def train_classifier(
    X: np.ndarray,
    y: np.ndarray,
    model_path: str = "app/cnki_model.pkl",
) -> dict:
    """Train XGBoost classifier with cross-validation."""
    from sklearn.model_selection import cross_val_score, train_test_split
    from sklearn.metrics import classification_report, roc_auc_score

    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss",
        )
        model_name = "XGBoost"
    except ImportError:
        print("XGBoost not available, using RandomForest...")
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
        model_name = "RandomForest"

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTraining {model_name} on {len(X_train)} samples ({len(X_test)} test)...")
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    print(f"\n--- Evaluation ---")
    print(classification_report(y_test, y_pred, target_names=["Human", "AI"]))
    print(f"AUC-ROC: {auc:.4f}")

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    print(f"5-fold CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Feature importance
    if hasattr(model, "feature_importances_"):
        importances = sorted(
            zip(FEATURE_NAMES, model.feature_importances_),
            key=lambda x: -x[1],
        )
        print("\nTop 10 features:")
        for name, imp in importances[:10]:
            print(f"  {name}: {imp:.4f}")

    # Save model
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to {model_path}")

    return {
        "model_type": model_name,
        "auc_roc": round(auc, 4),
        "cv_auc_mean": round(cv_scores.mean(), 4),
        "cv_auc_std": round(cv_scores.std(), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train CNKI AIGC classifier")
    parser.add_argument("--download", action="store_true", help="Download datasets")
    parser.add_argument("--train", action="store_true", help="Train model")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate model")
    parser.add_argument("--data-dir", default="./data", help="Dataset directory")
    parser.add_argument("--model-path", default="app/cnki_model.pkl", help="Model output path")
    args = parser.parse_args()

    if args.download:
        print("Downloading datasets...")
        os.makedirs(args.data_dir, exist_ok=True)

        try:
            from datasets import load_dataset
            print("Downloading HC3-Chinese...")
            dataset = load_dataset("Hello-SimpleAI/HC3-Chinese", split="train")
            dataset.save_to_disk(os.path.join(args.data_dir, "hc3_chinese"))
            print(f"Saved HC3-Chinese ({len(dataset)} samples) to {args.data_dir}/hc3_chinese")

            print("\nAttempting C-ReD download...")
            # C-ReD requires git clone: github.com/HeraldofLight/C-ReD
            print("C-ReD: please manually clone https://github.com/HeraldofLight/C-ReD")
            print(f"  git clone https://github.com/HeraldofLight/C-ReD {args.data_dir}/c-red")
        except ImportError:
            print("Install datasets: pip install datasets")
            print("\nManual download options:")
            print("1. HC3-Chinese: https://huggingface.co/datasets/Hello-SimpleAI/HC3-Chinese")
            print("2. C-ReD: https://github.com/HeraldofLight/C-ReD")

    if args.train:
        print("Loading data...")
        X, y = load_hc3_chinese(args.data_dir)

        if len(X) == 0:
            print("ERROR: No data loaded. Run --download first or provide local data.")
            sys.exit(1)

        result = train_classifier(X, y, args.model_path)
        print(f"\nTraining complete: {json.dumps(result, indent=2)}")

    if args.evaluate:
        model_path = args.model_path
        if not os.path.exists(model_path):
            print(f"Model not found: {model_path}. Run --train first.")
            sys.exit(1)

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        X, y = load_hc3_chinese(args.data_dir)
        if len(X) == 0:
            print("No evaluation data.")
            sys.exit(1)

        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, roc_auc_score

        _, X_test, _, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        print(classification_report(y_test, y_pred, target_names=["Human", "AI"]))
        print(f"AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}")


if __name__ == "__main__":
    main()
