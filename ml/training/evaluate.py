from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score


def evaluate_classifier(model, x_test, y_test) -> dict:
    predicted = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    roc_auc = None
    if len(set(y_test)) > 1:
        roc_auc = float(roc_auc_score(y_test, probabilities))

    return {
        "accuracy": float(accuracy_score(y_test, predicted)),
        "precision": float(precision_score(y_test, predicted, zero_division=0)),
        "recall": float(recall_score(y_test, predicted, zero_division=0)),
        "f1": float(f1_score(y_test, predicted, zero_division=0)),
        "roc_auc": roc_auc,
        "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
        "total_test_samples": int(len(predicted)),
        "num_predictions": int(len(predicted)),
        "up_predictions": int(np.sum(predicted == 1)),
        "down_predictions": int(np.sum(predicted == 0)),
        "actual_up": int(np.sum(np.asarray(y_test) == 1)),
        "actual_down": int(np.sum(np.asarray(y_test) == 0)),
    }
