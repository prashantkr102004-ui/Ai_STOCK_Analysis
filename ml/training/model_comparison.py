from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import argparse
import copy
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ml.backtesting.backtest import (
    add_buy_hold_equity,
    calculate_metrics,
    filter_backtest_data,
    simulate_trades,
)
from ml.training.train import (
    chronological_split,
    ensure_target,
    select_feature_columns,
    split_date_range,
    validate_processed_data,
    verify_no_leakage,
)


RANDOM_SEED = 42
PRODUCTION_MODEL_KEY = "xgboost_current"
DEFAULT_THRESHOLDS = [0.50, 0.55, 0.60, 0.65]
EXPERIMENT_DIR = Path("models/experiments")
CANDIDATE_DIR = Path("models/candidates")
COMPARISON_PATH = EXPERIMENT_DIR / "model_comparison.json"


@dataclass(frozen=True)
class Candidate:
    key: str
    name: str
    version: str
    estimator: object
    hyperparameters: dict


def metrics_from_predictions(y_true, y_pred, probabilities) -> dict:
    roc_auc = None
    if len(set(y_true)) > 1:
        roc_auc = float(roc_auc_score(y_true, probabilities))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def positive_probabilities(model, x_frame: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_frame)
        if proba.shape[1] == 1:
            return np.zeros(len(x_frame)) if int(model.classes_[0]) == 0 else np.ones(len(x_frame))
        positive_index = list(model.classes_).index(1) if hasattr(model, "classes_") and 1 in model.classes_ else 1
        return np.asarray(proba)[:, positive_index]
    return np.asarray(model.predict(x_frame), dtype=float)


def predict_with_threshold(probabilities: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    return (np.asarray(probabilities) >= threshold).astype(int)


def evaluate_model(model, x_frame: pd.DataFrame, y_true: pd.Series, threshold: float = 0.5) -> dict:
    start = time.perf_counter()
    probabilities = positive_probabilities(model, x_frame)
    predictions = predict_with_threshold(probabilities, threshold)
    inference_time = time.perf_counter() - start
    metrics = metrics_from_predictions(y_true, predictions, probabilities)
    metrics["inference_time_seconds"] = round(float(inference_time), 6)
    metrics["threshold"] = threshold
    return metrics


def target_distribution(y: pd.Series) -> dict:
    total = int(len(y))
    up = int((y == 1).sum())
    down = int((y == 0).sum())
    return {
        "up_observations": up,
        "down_observations": down,
        "up_percentage": round(up / total * 100, 2) if total else 0,
        "down_percentage": round(down / total * 100, 2) if total else 0,
    }


def class_weight_for(y: pd.Series) -> str | None:
    distribution = target_distribution(y)
    up = distribution["up_observations"]
    down = distribution["down_observations"]
    if not up or not down:
        return None
    ratio = max(up, down) / min(up, down)
    return "balanced" if ratio >= 1.5 else None


def make_candidates(y_train: pd.Series, include_current_xgboost: object | None = None) -> list[Candidate]:
    weight = class_weight_for(y_train)
    candidates = [
        Candidate(
            "baseline_majority",
            "Baseline Majority Class",
            "v1",
            DummyClassifier(strategy="most_frequent"),
            {"strategy": "most_frequent"},
        ),
        Candidate(
            "logistic_regression",
            "Logistic Regression",
            "v1",
            Pipeline(
                [
                    ("scaler", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            C=1.0,
                            class_weight=weight,
                            max_iter=2000,
                            random_state=RANDOM_SEED,
                        ),
                    ),
                ]
            ),
            {"C": 1.0, "class_weight": weight, "max_iter": 2000},
        ),
        Candidate(
            "random_forest",
            "Random Forest",
            "v1",
            RandomForestClassifier(
                n_estimators=160,
                max_depth=8,
                min_samples_split=8,
                min_samples_leaf=4,
                max_features="sqrt",
                class_weight=weight,
                n_jobs=-1,
                random_state=RANDOM_SEED,
            ),
            {
                "n_estimators": 160,
                "max_depth": 8,
                "min_samples_split": 8,
                "min_samples_leaf": 4,
                "max_features": "sqrt",
                "class_weight": weight,
            },
        ),
        Candidate(
            "xgboost_tuned",
            "XGBoost Tuned",
            "v2_candidate",
            XGBClassifier(
                n_estimators=220,
                max_depth=3,
                learning_rate=0.04,
                subsample=0.85,
                colsample_bytree=0.85,
                min_child_weight=3,
                reg_alpha=0.05,
                reg_lambda=1.5,
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=RANDOM_SEED,
            ),
            {
                "n_estimators": 220,
                "max_depth": 3,
                "learning_rate": 0.04,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "min_child_weight": 3,
                "reg_alpha": 0.05,
                "reg_lambda": 1.5,
            },
        ),
    ]
    if include_current_xgboost is not None:
        candidates.insert(
            3,
            Candidate(
                "xgboost_current",
                "XGBoost Current",
                "current",
                include_current_xgboost,
                {"source": "models/xgboost_model_latest.joblib"},
            ),
        )
    return candidates


def load_current_xgboost(model_dir: Path = Path("models")) -> object | None:
    latest = model_dir / "xgboost_model_latest.joblib"
    if not latest.exists():
        return None
    payload = joblib.load(latest)
    return payload.get("model")


def time_series_validation(model, x_train: pd.DataFrame, y_train: pd.Series, splits: int = 4) -> dict:
    tscv = TimeSeriesSplit(n_splits=min(splits, max(2, len(x_train) // 250)))
    fold_metrics = []
    for fold, (train_index, validation_index) in enumerate(tscv.split(x_train), start=1):
        fold_model = copy.deepcopy(model)
        fold_model.fit(x_train.iloc[train_index], y_train.iloc[train_index])
        metrics = evaluate_model(fold_model, x_train.iloc[validation_index], y_train.iloc[validation_index])
        fold_metrics.append({"fold": fold, **metrics})
    return {
        "method": "TimeSeriesSplit expanding-window validation",
        "folds": fold_metrics,
        "average_f1": float(np.mean([item["f1"] for item in fold_metrics])) if fold_metrics else None,
        "average_roc_auc": float(np.mean([item["roc_auc"] for item in fold_metrics if item["roc_auc"] is not None]))
        if any(item["roc_auc"] is not None for item in fold_metrics)
        else None,
    }


def tune_thresholds(model, x_validation: pd.DataFrame, y_validation: pd.Series) -> dict:
    probabilities = positive_probabilities(model, x_validation)
    rows = []
    for threshold in DEFAULT_THRESHOLDS:
        predictions = predict_with_threshold(probabilities, threshold)
        metrics = metrics_from_predictions(y_validation, predictions, probabilities)
        rows.append(
            {
                "threshold": threshold,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "up_predictions": int(predictions.sum()),
                "down_predictions": int(len(predictions) - predictions.sum()),
            }
        )
    selected = max(rows, key=lambda row: (row["f1"], row["precision"]))
    return {"tested_thresholds": rows, "selected_threshold": selected["threshold"], "selection_rule": "highest validation F1, precision tie-break"}


def calibration_summary(model, x_validation: pd.DataFrame, y_validation: pd.Series) -> dict:
    probabilities = positive_probabilities(model, x_validation)
    brier = float(brier_score_loss(y_validation, probabilities))
    fraction, mean_predicted = calibration_curve(y_validation, probabilities, n_bins=5, strategy="uniform")
    return {
        "brier_score": brier,
        "curve": [
            {"mean_predicted_probability": float(pred), "fraction_positive": float(actual)}
            for pred, actual in zip(mean_predicted, fraction)
        ],
        "note": "Lower Brier score indicates better probability calibration; calibration is evaluated on validation data only.",
    }


def feature_importance_for(model, features: list[str]) -> list[dict]:
    estimator = model.named_steps["model"] if isinstance(model, Pipeline) else model
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
        meaning = "Tree feature importance"
    elif hasattr(estimator, "coef_"):
        values = np.abs(estimator.coef_[0])
        meaning = "Standardized absolute coefficient magnitude"
    else:
        return []
    return [
        {"feature": feature, "importance": float(value), "meaning": meaning}
        for feature, value in sorted(zip(features, values), key=lambda item: item[1], reverse=True)
    ]


def backtest_model(
    model,
    features: list[str],
    processed: pd.DataFrame,
    symbol: str,
    start_date: str,
    end_date: str,
    threshold: float,
) -> dict:
    stock = filter_backtest_data(processed, symbol, start_date, end_date)
    predicted = stock.copy()
    probabilities = positive_probabilities(model, predicted[features].astype(float))
    predicted["probability_up"] = probabilities
    predicted["prediction"] = np.where(probabilities >= threshold, "UP", "DOWN")
    trades, equity = simulate_trades(predicted, initial_capital=100000.0, transaction_cost=0.001, slippage=0.0)
    equity = add_buy_hold_equity(stock, equity, 100000.0, 0.001, 0.0)
    metrics = calculate_metrics(symbol, stock, trades, equity, 100000.0, 0.001, 0.0)
    return {
        "symbol": symbol,
        "start_date": metrics["start_date"],
        "end_date": metrics["end_date"],
        "strategy_return": metrics["strategy_return"],
        "strategy_return_pct": metrics["strategy_return_pct"],
        "buy_hold_return": metrics["buy_hold_return"],
        "buy_hold_return_pct": metrics["buy_hold_return_pct"],
        "max_drawdown": metrics["max_drawdown"],
        "max_drawdown_pct": metrics["max_drawdown_pct"],
        "sharpe_ratio": metrics["sharpe_ratio"],
        "number_of_trades": metrics["number_of_trades"],
        "win_rate": metrics["win_rate"],
    }


def overfitting_warning(train_metrics: dict, validation_metrics: dict, test_metrics: dict) -> str | None:
    train_f1 = train_metrics.get("f1") or 0
    validation_f1 = validation_metrics.get("f1") or 0
    test_f1 = test_metrics.get("f1") or 0
    if train_f1 - min(validation_f1, test_f1) >= 0.15:
        return "Possible overfitting detected: training F1 is much stronger than validation/test F1."
    return None


def select_recommended_model(results: list[dict], current_key: str = PRODUCTION_MODEL_KEY) -> dict:
    current = next((item for item in results if item["model_key"] == current_key), None)
    eligible = [item for item in results if not item["model_key"].startswith("baseline")]
    if not eligible:
        return {"recommended_model": current_key, "production_model_changed": False, "reason": "No non-baseline candidates were available."}

    def score(item: dict) -> float:
        validation = item.get("validation_metrics", {})
        backtest = item.get("backtest", {})
        return (
            (validation.get("f1") or 0) * 0.45
            + (validation.get("roc_auc") or 0) * 0.35
            + max(backtest.get("sharpe_ratio") or 0, -2) * 0.05
            + (backtest.get("strategy_return") or 0) * 0.15
        )

    best = max(eligible, key=score)
    if current is None:
        return {"recommended_model": best["model_key"], "production_model_changed": False, "reason": "Current production model was unavailable for comparison; recommendation only."}

    margin = score(best) - score(current)
    current_drawdown = abs(current.get("backtest", {}).get("max_drawdown") or 0)
    best_drawdown = abs(best.get("backtest", {}).get("max_drawdown") or 0)
    clearly_better = (
        best["model_key"] != current_key
        and margin >= 0.02
        and (best.get("validation_metrics", {}).get("f1") or 0) >= (current.get("validation_metrics", {}).get("f1") or 0)
        and best_drawdown <= current_drawdown + 0.05
    )
    return {
        "recommended_model": best["model_key"] if clearly_better else current_key,
        "production_model_changed": False,
        "reason": "Recommendation only; production model is not switched automatically. "
        + (
            f"{best['model_name']} showed stronger validation/backtest evidence."
            if clearly_better
            else "Existing XGBoost remains production because no candidate was clearly superior across validation and risk-adjusted backtesting."
        ),
    }


def walk_forward_evaluation(model_factory, x_frame: pd.DataFrame, y: pd.Series, n_splits: int = 4) -> dict:
    splitter = TimeSeriesSplit(n_splits=min(n_splits, max(2, len(x_frame) // 300)))
    rows = []
    for fold, (train_index, test_index) in enumerate(splitter.split(x_frame), start=1):
        model = model_factory()
        model.fit(x_frame.iloc[train_index], y.iloc[train_index])
        rows.append({"fold": fold, **evaluate_model(model, x_frame.iloc[test_index], y.iloc[test_index])})
    return {
        "method": "Expanding-window walk-forward evaluation",
        "folds": rows,
        "average_f1": float(np.mean([row["f1"] for row in rows])) if rows else None,
        "average_roc_auc": float(np.mean([row["roc_auc"] for row in rows if row["roc_auc"] is not None]))
        if any(row["roc_auc"] is not None for row in rows)
        else None,
    }


def load_processed(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {path}")
    return pd.read_parquet(path)


def run_model_comparison(
    processed_path: str | Path = "ml/data/processed/all_stocks_features.parquet",
    output_path: str | Path = COMPARISON_PATH,
    backtest_symbol: str = "RELIANCE",
) -> dict:
    processed = load_processed(processed_path)
    validation_summary = validate_processed_data(processed)
    data = ensure_target(processed)
    features = select_feature_columns(data)
    verify_no_leakage(features)
    data = data.dropna(subset=features + ["Target"]).sort_values(["Date", "Symbol"]).reset_index(drop=True)
    train_df, validation_df, test_df = chronological_split(data)

    x_train, y_train = train_df[features].astype(float), train_df["Target"].astype(int)
    x_validation, y_validation = validation_df[features].astype(float), validation_df["Target"].astype(int)
    x_test, y_test = test_df[features].astype(float), test_df["Target"].astype(int)
    x_train_validation = pd.concat([x_train, x_validation], ignore_index=True)
    y_train_validation = pd.concat([y_train, y_validation], ignore_index=True)

    current_xgboost = load_current_xgboost()
    candidates = make_candidates(y_train, include_current_xgboost=current_xgboost)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    if backtest_symbol.upper() not in set(data["Symbol"]):
        backtest_symbol = str(sorted(data["Symbol"].unique())[0])
    backtest_start = split_date_range(test_df[test_df["Symbol"] == backtest_symbol.upper()])["start"]
    backtest_end = split_date_range(test_df[test_df["Symbol"] == backtest_symbol.upper()])["end"]

    results = []
    for candidate in candidates:
        model = candidate.estimator
        training_time = 0.0
        if candidate.key != "xgboost_current":
            start = time.perf_counter()
            if candidate.key == "xgboost_tuned":
                model.fit(x_train, y_train, eval_set=[(x_validation, y_validation)], verbose=False)
            else:
                model.fit(x_train, y_train)
            training_time = time.perf_counter() - start

        threshold_report = tune_thresholds(model, x_validation, y_validation)
        threshold = float(threshold_report["selected_threshold"])
        train_metrics = evaluate_model(model, x_train, y_train, threshold)
        validation_metrics = evaluate_model(model, x_validation, y_validation, threshold)
        test_metrics = evaluate_model(model, x_test, y_test, threshold)
        cv = time_series_validation(model, x_train_validation, y_train_validation)
        calibration = calibration_summary(model, x_validation, y_validation)
        backtest = backtest_model(model, features, processed, backtest_symbol, backtest_start, backtest_end, threshold)
        warning = overfitting_warning(train_metrics, validation_metrics, test_metrics)
        importance = feature_importance_for(model, features)[:20]

        model_path = CANDIDATE_DIR / f"{candidate.key}_{candidate.version}.joblib"
        metadata_path = CANDIDATE_DIR / f"{candidate.key}_{candidate.version}_metadata.json"
        if candidate.key != "baseline_majority":
            joblib.dump({"model": model, "features": features, "version": candidate.version, "model_key": candidate.key}, model_path)
        metadata = {
            "model_key": candidate.key,
            "model_name": candidate.name,
            "version": candidate.version,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "feature_list": features,
            "feature_count": len(features),
            "dataset_date_range": {
                "start": str(pd.to_datetime(data["Date"]).min().date()),
                "end": str(pd.to_datetime(data["Date"]).max().date()),
            },
            "hyperparameters": candidate.hyperparameters,
            "selected_threshold": threshold,
            "threshold_analysis": threshold_report,
            "train_metrics": train_metrics,
            "validation_metrics": validation_metrics,
            "test_metrics": test_metrics,
            "time_series_validation": cv,
            "calibration": calibration,
            "backtest": backtest,
            "training_time_seconds": round(float(training_time), 4),
            "overfitting_warning": warning,
            "feature_importance": importance,
            "model_path": str(model_path) if candidate.key != "baseline_majority" else None,
            "metadata_path": str(metadata_path),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        results.append(metadata)

    walk_forward = walk_forward_evaluation(
        lambda: XGBClassifier(
            n_estimators=120,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_SEED,
        ),
        x_train_validation,
        y_train_validation,
    )
    selection = select_recommended_model(results)
    production = next((item for item in results if item["model_key"] == PRODUCTION_MODEL_KEY), None) or results[0]

    comparison = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "production_model": PRODUCTION_MODEL_KEY,
        "production_model_name": production["model_name"],
        "recommended_model": selection["recommended_model"],
        "production_model_changed": selection["production_model_changed"],
        "selection_reason": selection["reason"],
        "validation_methodology": "Chronological 70/15/15 train-validation-test split per symbol; TimeSeriesSplit expanding-window validation on train+validation only.",
        "leakage_check": "Target is next trading day's close direction; feature columns containing future/next/target/label are rejected. Rolling features are generated from current and historical rows only.",
        "feature_count": len(features),
        "feature_list": features,
        "dataset_summary": validation_summary,
        "split_ranges": {
            "train": split_date_range(train_df),
            "validation": split_date_range(validation_df),
            "test": split_date_range(test_df),
        },
        "target_distribution": {
            "train": target_distribution(y_train),
            "validation": target_distribution(y_validation),
            "test": target_distribution(y_test),
        },
        "hyperparameters_tested": {item["model_key"]: item["hyperparameters"] for item in results},
        "walk_forward": walk_forward,
        "backtest_settings": {
            "symbol": backtest_symbol.upper(),
            "start_date": backtest_start,
            "end_date": backtest_end,
            "initial_capital": 100000,
            "transaction_cost": 0.001,
            "slippage": 0,
        },
        "models": results,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    return comparison


def print_summary(comparison: dict) -> None:
    print("Model comparison complete")
    print(f"Dataset: {comparison['dataset_summary']['earliest_date']} to {comparison['dataset_summary']['latest_date']}")
    print(f"Features: {comparison['feature_count']}")
    print(f"Backtest symbol: {comparison['backtest_settings']['symbol']}")
    print("Model | Validation F1 | Test F1 | ROC-AUC | Strategy Return | Sharpe")
    for item in comparison["models"]:
        test = item["test_metrics"]
        validation = item["validation_metrics"]
        backtest = item["backtest"]
        print(
            f"{item['model_name']} | {validation['f1']:.4f} | {test['f1']:.4f} | "
            f"{(test['roc_auc'] or 0):.4f} | {backtest['strategy_return_pct']:.2f}% | {backtest['sharpe_ratio']}"
        )
    print(f"Recommended production model: {comparison['recommended_model']}")
    print(comparison["selection_reason"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare AI MarketGuard model candidates without touching the final test set during tuning.")
    parser.add_argument("--processed-path", default="ml/data/processed/all_stocks_features.parquet")
    parser.add_argument("--output-path", default=str(COMPARISON_PATH))
    parser.add_argument("--backtest-symbol", default="RELIANCE")
    args = parser.parse_args()
    comparison = run_model_comparison(args.processed_path, args.output_path, args.backtest_symbol)
    print_summary(comparison)


if __name__ == "__main__":
    main()
