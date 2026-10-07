from datetime import datetime, timezone
from statistics import mean, pstdev

from sqlmodel import Session, select

from app.models.behavioral_baseline import BehavioralBaseline
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device


MINIMUM_BASELINE_SAMPLES = 10


def _safe_std(values: list[float]) -> float:
    """
    Population standard deviation.

    A zero standard deviation is valid when an employee's
    behavior has not varied during the training period.
    """

    if len(values) <= 1:
        return 0.0

    return pstdev(values)


def _z_score(
    value: float,
    average: float,
    standard_deviation: float,
) -> float:
    """
    Calculate a safe z-score.

    If there is no observed variation, return 0.
    The detection engine will handle constant features
    separately.
    """

    if standard_deviation <= 0:
        return 0.0

    return (
        value - average
    ) / standard_deviation


def get_employee_windows(
    employee_id: int,
    session: Session,
    session_id: str | None = None,
) -> list[BehavioralWindow]:
    """
    Retrieve behavioral windows belonging to an employee.

    Employee identity is resolved through the authenticated
    device relationship rather than trusting client input.
    """

    statement = (
        select(BehavioralWindow)
        .join(
            Device,
            BehavioralWindow.device_id == Device.id,
        )
        .where(
            Device.employee_id == employee_id
        )
    )
    if session_id is not None:
        statement = statement.where(
            BehavioralWindow.session_id == session_id
        )
    statement = statement.order_by(
        BehavioralWindow.window_start
    )

    return list(
        session.exec(statement).all()
    )


def calculate_baseline(
    employee_id: int,
    session: Session,
    session_id: str | None = None,
) -> BehavioralBaseline:
    """
    Calculate and persist the behavioral baseline
    for one employee.
    """

    windows = get_employee_windows(
        employee_id,
        session,
        session_id=session_id,
    )

    if len(windows) < MINIMUM_BASELINE_SAMPLES:
        raise ValueError(
            f"At least {MINIMUM_BASELINE_SAMPLES} "
            f"behavioral windows are required to "
            f"build a baseline. "
            f"Currently available: {len(windows)}"
        )

    # ---------------------------------------------
    # Extract historical features
    # ---------------------------------------------

    total_events = [
        float(w.total_events)
        for w in windows
    ]

    files_created = [
        float(w.files_created)
        for w in windows
    ]

    files_modified = [
        float(w.files_modified)
        for w in windows
    ]

    files_deleted = [
        float(w.files_deleted)
        for w in windows
    ]

    files_moved = [
        float(w.files_moved)
        for w in windows
    ]

    sensitive_events = [
        float(w.sensitive_events)
        for w in windows
    ]

    sensitive_ratio = [
        float(w.sensitive_ratio)
        for w in windows
    ]

    data_volume = [
        float(w.total_data_volume)
        for w in windows
    ]

    unique_extensions = [
        float(w.unique_extensions)
        for w in windows
    ]

    directory_breadth = [
        float(w.directory_breadth)
        for w in windows
    ]

    activity_rate = [
        float(w.activity_rate)
        for w in windows
    ]

    after_hours_ratio = (
        sum(
            1
            for w in windows
            if w.after_hours
        )
        / len(windows)
    )

    # ---------------------------------------------
    # Find existing baseline
    # ---------------------------------------------

    baseline = session.exec(
        select(BehavioralBaseline).where(
            BehavioralBaseline.employee_id
            == employee_id
        )
    ).first()

    if baseline is None:
        baseline = BehavioralBaseline(
            employee_id=employee_id
        )

    # ---------------------------------------------
    # Store mean + standard deviation
    # ---------------------------------------------

    baseline.avg_events_per_window = mean(
        total_events
    )
    baseline.std_events_per_window = _safe_std(
        total_events
    )

    baseline.avg_files_created = mean(
        files_created
    )
    baseline.std_files_created = _safe_std(
        files_created
    )

    baseline.avg_files_modified = mean(
        files_modified
    )
    baseline.std_files_modified = _safe_std(
        files_modified
    )

    baseline.avg_files_deleted = mean(
        files_deleted
    )
    baseline.std_files_deleted = _safe_std(
        files_deleted
    )

    baseline.avg_files_moved = mean(
        files_moved
    )
    baseline.std_files_moved = _safe_std(
        files_moved
    )

    baseline.avg_sensitive_events = mean(
        sensitive_events
    )
    baseline.std_sensitive_events = _safe_std(
        sensitive_events
    )

    baseline.avg_sensitive_ratio = mean(
        sensitive_ratio
    )
    baseline.std_sensitive_ratio = _safe_std(
        sensitive_ratio
    )

    baseline.avg_data_volume = mean(
        data_volume
    )
    baseline.std_data_volume = _safe_std(
        data_volume
    )

    baseline.avg_unique_extensions = mean(
        unique_extensions
    )
    baseline.std_unique_extensions = _safe_std(
        unique_extensions
    )

    baseline.avg_directory_breadth = mean(
        directory_breadth
    )
    baseline.std_directory_breadth = _safe_std(
        directory_breadth
    )

    baseline.avg_activity_rate = mean(
        activity_rate
    )
    baseline.std_activity_rate = _safe_std(
        activity_rate
    )

    baseline.after_hours_ratio = (
        after_hours_ratio
    )

    baseline.sample_count = len(windows)

    baseline.last_trained_at = (
        datetime.now(timezone.utc)
    )

    session.add(baseline)
    session.commit()
    session.refresh(baseline)

    return baseline


def calculate_deviation_features(
    window: BehavioralWindow,
    baseline: BehavioralBaseline,
) -> dict:
    """
    Convert one behavioral window into deviation features.

    These features will eventually become inputs to
    the anomaly detection model.
    """

    return {
        "event_volume_zscore": _z_score(
            window.total_events,
            baseline.avg_events_per_window,
            baseline.std_events_per_window,
        ),

        "files_created_zscore": _z_score(
            window.files_created,
            baseline.avg_files_created,
            baseline.std_files_created,
        ),

        "files_modified_zscore": _z_score(
            window.files_modified,
            baseline.avg_files_modified,
            baseline.std_files_modified,
        ),

        "files_deleted_zscore": _z_score(
            window.files_deleted,
            baseline.avg_files_deleted,
            baseline.std_files_deleted,
        ),

        "files_moved_zscore": _z_score(
            window.files_moved,
            baseline.avg_files_moved,
            baseline.std_files_moved,
        ),

        "sensitive_events_zscore": _z_score(
            window.sensitive_events,
            baseline.avg_sensitive_events,
            baseline.std_sensitive_events,
        ),

        "sensitive_ratio_zscore": _z_score(
            window.sensitive_ratio,
            baseline.avg_sensitive_ratio,
            baseline.std_sensitive_ratio,
        ),

        "data_volume_zscore": _z_score(
            window.total_data_volume,
            baseline.avg_data_volume,
            baseline.std_data_volume,
        ),

        "extension_diversity_zscore": _z_score(
            window.unique_extensions,
            baseline.avg_unique_extensions,
            baseline.std_unique_extensions,
        ),

        "directory_breadth_zscore": _z_score(
            window.directory_breadth,
            baseline.avg_directory_breadth,
            baseline.std_directory_breadth,
        ),

        "activity_rate_zscore": _z_score(
            window.activity_rate,
            baseline.avg_activity_rate,
            baseline.std_activity_rate,
        ),

        "after_hours_deviation": (
            1.0
            if window.after_hours
            and baseline.after_hours_ratio < 0.2
            else 0.0
        ),
    }