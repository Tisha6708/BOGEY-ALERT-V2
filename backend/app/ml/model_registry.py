from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "artifacts" / "models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class ModelRegistry:
    """
    Handles persistence and retrieval of trained
    BOGEY-ALERT ML models.

    Supports:
    - employee-specific models
    - global behavioral models
    """

    MODEL_NAME = "behavioral_isolation_forest"

    GLOBAL_MODEL_PREFIX = (
        "behavioral_isolation_forest_global_"
    )

    def __init__(self):
        self.model_dir = MODEL_DIR

    # ========================================================
    # EMPLOYEE MODEL
    # ========================================================

    def save(
        self,
        model: Any,
        employee_id: int,
        metadata: dict | None = None,
    ) -> dict:

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        version = (
            f"employee_{employee_id}_{timestamp}"
        )

        model_path = (
            self.model_dir
            / f"{self.MODEL_NAME}_{version}.joblib"
        )

        artifact = {
            "model": model,
            "model_name": self.MODEL_NAME,
            "version": version,
            "employee_id": employee_id,
            "scope": "employee",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "metadata": metadata or {},
        }

        joblib.dump(
            artifact,
            model_path,
        )

        return {
            "model_name": self.MODEL_NAME,
            "version": version,
            "employee_id": employee_id,
            "path": str(model_path),
        }

    # ========================================================
    # GLOBAL MODEL
    # ========================================================

    def save_global(
        self,
        model: Any,
        metadata: dict | None = None,
    ) -> dict:
        """
        Persist the global behavioral model.

        The global model operates on employee-relative
        deviation features, so it can be shared across
        employees.
        """

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        version = (
            f"global_{timestamp}"
        )

        model_path = (
            self.model_dir
            / f"{self.GLOBAL_MODEL_PREFIX}"
            f"{timestamp}.joblib"
        )

        artifact = {
            "model": model,
            "model_name": self.MODEL_NAME,
            "version": version,
            "employee_id": None,
            "scope": "global",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "metadata": metadata or {},
        }

        joblib.dump(
            artifact,
            model_path,
        )

        return {
            "model_name": self.MODEL_NAME,
            "version": version,
            "scope": "global",
            "path": str(model_path),
        }

    def load(
        self,
        model_path: str | Path,
    ) -> dict:

        path = Path(model_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {path}"
            )

        artifact = joblib.load(path)

        required_fields = {
            "model",
            "model_name",
            "version",
            "created_at",
        }

        missing = (
            required_fields
            - artifact.keys()
        )

        if missing:
            raise ValueError(
                "Invalid model artifact. "
                f"Missing: {sorted(missing)}"
            )

        return artifact

    # ========================================================
    # GLOBAL MODEL LOOKUP
    # ========================================================

    def latest_global_model(self) -> Path | None:
        """
        Return the newest global behavioral model.
        """

        models = sorted(
            self.model_dir.glob(
                f"{self.GLOBAL_MODEL_PREFIX}*.joblib"
            )
        )

        if not models:
            return None

        return models[-1]

    # ========================================================
    # EMPLOYEE MODEL LOOKUP
    # ========================================================

    def list_employee_models(
        self,
        employee_id: int,
    ) -> list[Path]:

        pattern = (
            f"{self.MODEL_NAME}_"
            f"employee_{employee_id}_*.joblib"
        )

        return sorted(
            self.model_dir.glob(pattern)
        )

    def latest_employee_model(
        self,
        employee_id: int,
    ) -> Path | None:

        models = self.list_employee_models(
            employee_id
        )

        if not models:
            return None

        return models[-1]