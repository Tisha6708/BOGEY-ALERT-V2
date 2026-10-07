from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_score: float
    raw_score: float


class BehavioralAnomalyDetector:
    """
    Isolation Forest based behavioral anomaly detector.

    The model detects unusual behavioral patterns.
    It does NOT determine whether an employee is malicious.
    """

    FEATURE_NAMES = [
        "event_volume_zscore",
        "files_created_zscore",
        "files_modified_zscore",
        "files_deleted_zscore",
        "files_moved_zscore",
        "sensitive_events_zscore",
        "sensitive_ratio_zscore",
        "data_volume_zscore",
        "extension_diversity_zscore",
        "directory_breadth_zscore",
        "activity_rate_zscore",
        "after_hours_deviation",
    ]

    def __init__(
        self,
        contamination: float = 0.05,
        random_state: int = 42,
    ):
        """
        contamination represents the expected proportion
        of anomalous training samples.

        0.05 means approximately 5% of training samples
        are expected to be anomalous.
        """

        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )

        self.is_fitted = False

    def _vectorize(
        self,
        features: dict,
    ) -> np.ndarray:
        """
        Convert deviation features into the exact
        feature vector expected by the model.
        """

        return np.array(
            [
                features[name]
                for name in self.FEATURE_NAMES
            ],
            dtype=float,
        )

    def fit(
        self,
        training_features: list[dict],
    ) -> None:
        """
        Train the Isolation Forest using historical
        behavioral deviation features.
        """

        if len(training_features) < 10:
            raise ValueError(
                "At least 10 training samples are required "
                "to train the anomaly detector."
            )

        X = np.array(
            [
                self._vectorize(features)
                for features in training_features
            ]
        )

        self.model.fit(X)

        self.is_fitted = True

    def predict(
        self,
        features: dict,
    ) -> AnomalyResult:
        """
        Predict whether the supplied behavioral
        window is anomalous.
        """

        if not self.is_fitted:
            raise RuntimeError(
                "The anomaly detector has not been trained."
            )

        X = self._vectorize(features).reshape(1, -1)

        # Convert NumPy scalar types to native Python types.
        prediction = int(self.model.predict(X)[0])
        raw_score = float(self.model.score_samples(X)[0])

        is_anomaly = prediction == -1

        return AnomalyResult(
            is_anomaly=bool(is_anomaly),
            anomaly_score=self._normalize_score(raw_score),
            raw_score=raw_score,
        )

    @staticmethod
    def _normalize_score(
        raw_score: float,
    ) -> float:
        """
        Convert Isolation Forest's raw score into a
        bounded anomaly indicator.

        IMPORTANT:
        This is NOT a probability.

        It is only a normalized presentation score.
        """

        # Isolation Forest score_samples is generally
        # negative, with more negative values indicating
        # greater abnormality.

        normalized = 1.0 / (
            1.0 + np.exp(
                raw_score * 5.0
            )
        )

        return float(
            np.clip(
                normalized,
                0.0,
                1.0,
            )
        )