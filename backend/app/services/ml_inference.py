from sqlmodel import Session

from app.ml.model_registry import ModelRegistry
from app.models.behavioral_baseline import BehavioralBaseline
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.services.baseline import calculate_deviation_features


def detect_behavioral_anomaly(
    window: BehavioralWindow,
    baseline: BehavioralBaseline,
    session: Session,
):
    # ========================================================
    # DEVICE / EMPLOYEE IDENTITY
    # ========================================================

    device = session.get(
        Device,
        window.device_id,
    )

    if not device:
        raise ValueError(
            f"Device {window.device_id} not found."
        )

    employee_id = device.employee_id

    # ========================================================
    # BASELINE OWNERSHIP
    # ========================================================

    if baseline.employee_id != employee_id:
        raise ValueError(
            "Behavioral baseline does not belong to "
            "the employee associated with this "
            "behavioral window."
        )

    # ========================================================
    # LOAD GLOBAL MODEL
    # ========================================================

    registry = ModelRegistry()

    model_path = registry.latest_global_model()

    if model_path is None:
        raise ValueError(
            "No global behavioral model has been trained."
        )

    artifact = registry.load(
        model_path
    )

    if artifact.get("scope") != "global":
        raise ValueError(
            "Invalid behavioral model scope. "
            "Expected global model."
        )

    detector = artifact["model"]

    # ========================================================
    # CALCULATE EMPLOYEE-RELATIVE FEATURES
    # ========================================================

    features = calculate_deviation_features(
        window=window,
        baseline=baseline,
    )

    # ========================================================
    # OBSERVED ACTIVITY
    # ========================================================

    features["observed_activity"] = (
        window.observed_activity
    )

    # ========================================================
    # RUN ML DETECTION
    # ========================================================

    result = detector.predict(
        features
    )

    return {
        "employee_id": employee_id,
        "device_id": window.device_id,
        "window_id": window.id,

        "model_name": artifact["model_name"],
        "model_version": artifact["version"],

        "is_anomaly": result.is_anomaly,
        "anomaly_score": result.anomaly_score,
        "raw_score": result.raw_score,

        "features": features,

        "observed_activity": (
            window.observed_activity
        ),
    }