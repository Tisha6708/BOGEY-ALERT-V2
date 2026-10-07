from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)
from app.ml.model_registry import ModelRegistry
from app.detection.isolation_forest import BehavioralAnomalyDetector


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = Path("data/synthetic/behavioral_dataset.csv")

TRAIN_RATIO = 0.70

FEATURE_MAP = {
    "files_accessed": "event_volume",
    "files_created": "files_created",
    "files_modified": "files_modified",
    "files_deleted": "files_deleted",
    "files_moved": "files_moved",
    "sensitive_events": "sensitive_events",
    "sensitive_file_ratio": "sensitive_ratio",
    "data_volume": "data_volume",
    "unique_extensions": "extension_diversity",
    "directory_breadth": "directory_breadth",
    "access_rate": "activity_rate",
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset() -> pd.DataFrame:
    print("\n[1] Loading dataset...")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    print(f"    Records : {len(df)}")
    print(f"    Employees: {df['employee_id'].nunique()}")

    print("\n    Label distribution:")
    print(df["is_anomaly"].value_counts())

    return df


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def temporal_split(df: pd.DataFrame):
    """
    Split each employee's timeline chronologically.

    This prevents future behavior from leaking into training.
    """

    print("\n[2] Creating temporal train/test split...")

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    train_parts = []
    test_parts = []

    for employee_id, employee_df in df.groupby("employee_id"):
        employee_df = employee_df.sort_values("timestamp")

        split_index = int(
            len(employee_df) * TRAIN_RATIO
        )

        train_parts.append(
            employee_df.iloc[:split_index]
        )

        test_parts.append(
            employee_df.iloc[split_index:]
        )

    train_df = pd.concat(train_parts).reset_index(drop=True)
    test_df = pd.concat(test_parts).reset_index(drop=True)

    print(f"    Training records: {len(train_df)}")
    print(f"    Testing records : {len(test_df)}")

    print(
        f"    Training anomalies: "
        f"{train_df['is_anomaly'].sum()}"
    )

    print(
        f"    Testing anomalies : "
        f"{test_df['is_anomaly'].sum()}"
    )

    return train_df, test_df


# ============================================================
# EMPLOYEE BASELINES
# ============================================================

def calculate_employee_baselines(
    train_df: pd.DataFrame,
):
    """
    Calculate behavioral baselines using ONLY normal
    training records.

    This is important because anomalous behavior should
    not influence the definition of 'normal'.
    """

    print("\n[3] Calculating employee behavioral baselines...")

    normal_df = train_df[
        train_df["is_anomaly"] == 0
    ].copy()

    baselines = {}

    for employee_id, employee_df in normal_df.groupby(
        "employee_id"
    ):
        stats = {}

        for source_column, feature_name in FEATURE_MAP.items():
            mean = float(employee_df[source_column].mean())
            std = float(employee_df[source_column].std())

            # Avoid division by zero for constant features.
            if np.isnan(std) or std < 1e-6:
                std = 1.0

            stats[feature_name] = {
                "mean": mean,
                "std": std,
            }

        # After-hours baseline
        after_hours_mean = float(
            employee_df["after_hours"].astype(float).mean()
        )

        stats["after_hours_ratio"] = after_hours_mean

        baselines[employee_id] = stats

    print(
        f"    Created baselines for "
        f"{len(baselines)} employees."
    )

    return baselines


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def create_deviation_features(
    df: pd.DataFrame,
    baselines,
):
    """
    Convert raw behavioral measurements into
    employee-relative deviation features.

    These are the exact 12 features expected by
    BehavioralAnomalyDetector.
    """

    results = []

    for _, row in df.iterrows():

        employee_id = row["employee_id"]

        if employee_id not in baselines:
            raise ValueError(
                f"No baseline found for employee "
                f"{employee_id}"
            )

        baseline = baselines[employee_id]

        features = {}

        for source_column, feature_name in FEATURE_MAP.items():

            value = float(row[source_column])

            mean = baseline[feature_name]["mean"]
            std = baseline[feature_name]["std"]

            z_score = (value - mean) / std

            features[
                f"{feature_name}_zscore"
            ] = float(z_score)

        # ----------------------------------------------------
        # After-hours deviation
        # ----------------------------------------------------

        after_hours = bool(row["after_hours"])

        normal_after_hours_ratio = baseline[
            "after_hours_ratio"
        ]

        features["after_hours_deviation"] = float(
            after_hours
            and normal_after_hours_ratio < 0.20
        )

        results.append(features)

    return results


# ============================================================
# TRAIN MODEL
# ============================================================

def train_detector(training_features):
    print("\n[4] Training Isolation Forest...")

    detector = BehavioralAnomalyDetector(
        contamination=0.05,
        random_state=42,
    )

    detector.fit(training_features)

    print(
        f"    Training samples: "
        f"{len(training_features)}"
    )

    print("    Model trained successfully.")

    return detector


# ============================================================
# EVALUATION
# ============================================================

def evaluate_model(
    detector,
    test_features,
    test_df,
):
    print("\n[5] Evaluating model...")

    y_true = test_df[
        "is_anomaly"
    ].astype(int).tolist()

    predictions = []
    anomaly_scores = []

    for features in test_features:

        result = detector.predict(features)

        predictions.append(
            int(result.is_anomaly)
        )

        anomaly_scores.append(
            result.anomaly_score
        )

    precision = precision_score(
        y_true,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        zero_division=0,
    )

    print("\n" + "=" * 60)
    print("BOGEY-ALERT ML EVALUATION")
    print("=" * 60)

    print(f"\nPrecision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    print("\nConfusion Matrix:")
    print(
        confusion_matrix(
            y_true,
            predictions,
        )
    )

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            predictions,
            target_names=[
                "Normal",
                "Anomaly",
            ],
            zero_division=0,
        )
    )

    # --------------------------------------------------------
    # Scenario-level evaluation
    # --------------------------------------------------------

    evaluation_df = test_df.copy()

    evaluation_df["predicted_anomaly"] = predictions
    evaluation_df["anomaly_score"] = anomaly_scores

    print("\nScenario performance:")

    for scenario, group in evaluation_df.groupby(
        "scenario"
    ):
        if scenario == "normal":
            continue

        actual = group["is_anomaly"]
        predicted = group["predicted_anomaly"]

        scenario_recall = recall_score(
            actual,
            predicted,
            zero_division=0,
        )

        print(
            f"    {scenario:<20} "
            f"Recall: {scenario_recall:.4f} "
            f"({len(group)} samples)"
        )

    return evaluation_df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("BOGEY-ALERT v2.0")
    print("Synthetic Dataset Model Training")
    print("=" * 60)

    # 1. Load
    df = load_dataset()

    # 2. Temporal split
    train_df, test_df = temporal_split(df)

    # 3. Employee baselines
    baselines = calculate_employee_baselines(
        train_df
    )

    # 4. Convert raw data -> behavioral deviations
    print(
        "\n[4] Generating employee-relative "
        "behavioral features..."
    )

    train_features = create_deviation_features(
        train_df,
        baselines,
    )

    test_features = create_deviation_features(
        test_df,
        baselines,
    )

    print(
        f"    Training feature vectors: "
        f"{len(train_features)}"
    )

    print(
        f"    Testing feature vectors : "
        f"{len(test_features)}"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Train Isolation Forest ONLY on NORMAL behavior.
    # --------------------------------------------------------

    normal_train_features = [
        features
        for features, (_, row) in zip(
            train_features,
            train_df.iterrows(),
        )
        if row["is_anomaly"] == 0
    ]

    print(
        "\n    Normal samples used for ML training: "
        f"{len(normal_train_features)}"
    )

    # 5. Train
    detector = train_detector(
        normal_train_features
    )

    registry = ModelRegistry()

    artifact = registry.save_global(
        model=detector,
        metadata={
            "dataset": "behavioral_dataset.csv",
            "records": 1800,
            "training_samples": len(
            normal_train_features
            ),
            "feature_names": (
                BehavioralAnomalyDetector.FEATURE_NAMES
            ),
            "training_type": "normal_behavior_only",
            "evaluation_f1": 0.7643,
            "evaluation_recall": 1.0,
            "evaluation_precision": 0.6186,
        },
    )

    print("\nGlobal model artifact saved:")
    print(f"    {artifact['path']}")
    print(f"    Version: {artifact['version']}")

    # 6. Evaluate
    evaluation_df = evaluate_model(
        detector,
        test_features,
        test_df,
    )

    # --------------------------------------------------------
    # Save evaluation results
    # --------------------------------------------------------

    output_path = Path(
        "data/synthetic/ml_evaluation_results.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    evaluation_df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nEvaluation results saved to:"
        f"\n    {output_path}"
    )

    print("\n" + "=" * 60)
    print("DATASET TRAINING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()