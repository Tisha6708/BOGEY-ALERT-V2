from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from app.models.behavioral_window import BehavioralWindow
from app.models.role_policy import RolePolicy


POLICY_TIMEZONE = ZoneInfo("Asia/Kolkata")


@dataclass
class PolicyEvaluation:
    violated: bool
    violations: list[str]
    matched_activities: list[str]


def _parse_time(value: str) -> time:
    """
    Convert HH:MM policy configuration into a time object.
    """

    try:
        hour, minute = value.split(":")

        return time(
            hour=int(hour),
            minute=int(minute),
        )

    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid working-hour value '{value}'. "
            "Expected HH:MM."
        )


def _to_policy_timezone(
    activity_time: datetime,
) -> datetime:
    """
    Convert stored activity timestamps into the timezone
    used by organizational policies.

    Backend timestamps are expected to be UTC.
    Policies are evaluated in Asia/Kolkata.
    """

    if activity_time.tzinfo is None:
        activity_time = activity_time.replace(
            tzinfo=timezone.utc
        )

    return activity_time.astimezone(
        POLICY_TIMEZONE
    )


def _is_within_working_hours(
    activity_time: datetime,
    policy: RolePolicy,
) -> bool:

    start = _parse_time(
        policy.working_hours_start
    )

    end = _parse_time(
        policy.working_hours_end
    )

    current = activity_time.time()

    if start == end:
        return True

    if start < end:
        return start <= current <= end

    return current >= start or current <= end


def evaluate_window_against_policy(
    window: BehavioralWindow,
    policy: RolePolicy,
) -> PolicyEvaluation:

    violations = []
    matched_activities = []

    # ========================================================
    # 1. OBSERVED FILE ACTIVITIES
    # ========================================================

    observed_activities = {
        activity.strip().lower()
        for activity in window.observed_activity.split(",")
        if activity.strip()
    }

    allowed_activities = {
        activity.strip().lower()
        for activity in policy.allowed_activities.split(",")
        if activity.strip()
    }

    for activity in sorted(observed_activities):

        if activity in allowed_activities:
            matched_activities.append(activity)

        else:
            violations.append(
                f"Activity '{activity}' is not permitted "
                f"by the employee's role policy."
            )

    # ========================================================
    # 2. SENSITIVE DATA ACCESS
    # ========================================================

    if (
        window.sensitive_events > 0
        and not policy.sensitive_data_access_allowed
    ):
        violations.append(
            "Sensitive-data activity was observed, but the "
            "employee's role policy does not permit sensitive "
            "data access."
        )

    # ========================================================
    # 3. DATA VOLUME
    # ========================================================

    if (
        policy.max_data_volume_per_window > 0
        and window.total_data_volume
        > policy.max_data_volume_per_window
    ):
        violations.append(
            "Data volume exceeded the maximum permitted "
            "amount for this role."
        )

    # ========================================================
    # 4. SENSITIVE EVENT COUNT
    # ========================================================

    if (
        policy.max_sensitive_events_per_window > 0
        and window.sensitive_events
        > policy.max_sensitive_events_per_window
    ):
        violations.append(
            "Sensitive-event volume exceeded the maximum "
            "permitted amount for this role."
        )

    # ========================================================
    # 5. WORKING HOURS / WEEKEND
    # ========================================================

    activity_time = _to_policy_timezone(
        window.window_end
    )

    is_weekend = (
        activity_time.weekday() >= 5
    )

    if is_weekend:

        if not policy.weekend_activity_allowed:
            violations.append(
                "Activity occurred on a weekend, but weekend "
                "activity is not permitted for this role."
            )

    else:

        within_hours = _is_within_working_hours(
            activity_time=activity_time,
            policy=policy,
        )

        if not within_hours:
            violations.append(
                "Activity occurred outside the configured "
                "working hours for this role."
            )

    return PolicyEvaluation(
        violated=len(violations) > 0,
        violations=violations,
        matched_activities=matched_activities,
    )