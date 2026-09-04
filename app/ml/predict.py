from pathlib import Path

import joblib
import pandas as pd
from uuid import uuid4

from app.database.predictions import save_prediction
from app.ml.features import FEATURE_ORDER


MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
MODEL_PATH = MODEL_DIR / "recovery_model.pkl"
SCALER_PATH = MODEL_DIR / "recovery_scaler.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

MODEL_VERSION = "v1"

scaler_feature_order = tuple(
    getattr(scaler, "feature_names_in_", ())
)
if scaler_feature_order and scaler_feature_order != FEATURE_ORDER:
    raise RuntimeError(
        "ML scaler feature order does not match the application feature order"
    )

if getattr(scaler, "n_features_in_", len(FEATURE_ORDER)) != len(FEATURE_ORDER):
    raise RuntimeError("ML scaler feature count does not match FEATURE_ORDER")

if getattr(model, "n_features_in_", len(FEATURE_ORDER)) != len(FEATURE_ORDER):
    raise RuntimeError("ML model feature count does not match FEATURE_ORDER")


def predict_recovery(features: dict, case_id: str):
    missing_features = [
        name for name in FEATURE_ORDER
        if name not in features
    ]
    unexpected_features = [
        name for name in features
        if name not in FEATURE_ORDER
    ]

    if missing_features:
        raise ValueError(
            "Missing required ML features: "
            + ", ".join(missing_features)
        )

    if unexpected_features:
        raise ValueError(
            "Unexpected ML features: "
            + ", ".join(unexpected_features)
        )

    df = pd.DataFrame(
        [[features[name] for name in FEATURE_ORDER]],
        columns=FEATURE_ORDER,
    )

    scaled_features = scaler.transform(df)

    probability = model.predict_proba(scaled_features)[0][1]

    predicted_class = int(probability >= 0.50)

    save_prediction(
        prediction_id=str(uuid4()),
        case_id=case_id,
        model_version=MODEL_VERSION,
        recovery_probability=float(probability),
        predicted_class=predicted_class,
    )

    return probability