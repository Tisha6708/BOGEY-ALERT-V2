from sqlmodel import Session

from app.detection.isolation_forest import (
    BehavioralAnomalyDetector,
)
from app.ml.model_registry import ModelRegistry
from app.services.baseline import (
    calculate_baseline,
    calculate_deviation_features,
    get_employee_windows,
)


MINIMUM_TRAINING_SAMPLES = 10


def train_employee_detector(
    employee_id: int,
    session: Session,
) -> dict:
    """
    Train and persist an employee-specific
    behavioral anomaly detector.

    Pipeline:

        Behavioral Windows
                ↓
        Employee Baseline
                ↓
        Deviation Features
                ↓
        Isolation Forest
                ↓
        Model Registry
                ↓
        Persistent Artifact
    """

    # --------------------------------------------------
    # 1. Retrieve historical windows
    # --------------------------------------------------

    windows = get_employee_windows(
        employee_id=employee_id,
        session=session,
    )

    if len(windows) < MINIMUM_TRAINING_SAMPLES:
        raise ValueError(
            f"At least {MINIMUM_TRAINING_SAMPLES} "
            f"behavioral windows are required for training. "
            f"Currently available: {len(windows)}"
        )

    # --------------------------------------------------
    # 2. Build / refresh employee baseline
    # --------------------------------------------------

    baseline = calculate_baseline(
        employee_id=employee_id,
        session=session,
    )

    # --------------------------------------------------
    # 3. Generate deviation features
    # --------------------------------------------------

    training_features = []

    for window in windows:

        features = calculate_deviation_features(
            window=window,
            baseline=baseline,
        )

        training_features.append(features)

    # --------------------------------------------------
    # 4. Train Isolation Forest
    # --------------------------------------------------

    detector = BehavioralAnomalyDetector()

    detector.fit(
        training_features
    )

    # --------------------------------------------------
    # 5. Persist trained model
    # --------------------------------------------------

    registry = ModelRegistry()

    metadata = {
        "training_samples": len(
            training_features
        ),
        "baseline_samples": baseline.sample_count,
        "feature_names": (
            detector.FEATURE_NAMES
        ),
    }

    artifact = registry.save(
        model=detector,
        employee_id=employee_id,
        metadata=metadata,
    )

    return artifact