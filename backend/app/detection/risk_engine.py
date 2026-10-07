from dataclasses import dataclass


@dataclass
class RiskResult:
    risk_score: int
    risk_level: str
    reasons: list[str]
    authorization_context: dict | None = None
    policy_context: dict | None = None


class RiskEngine:
    """
    Hybrid insider-threat risk engine.

    Combines:
    - ML behavioral anomaly
    - Sensitive-data activity
    - Data volume
    - Activity burst
    - After-hours activity
    - Explicitly observed filesystem activity
    - Role-policy violations
    - Authorization context

    Important:
    The engine does NOT claim that a file was transferred or read
    unless the endpoint actually reports such an event.

    Authorization is contextual evidence, not a mechanism that
    disables detection.

    Role policies define what is normally permitted for an employee's
    role. A policy violation increases risk but does not automatically
    determine the final verdict.
    """

    def evaluate(
        self,
        anomaly_result,
        features,
        authorization=None,
        policy_evaluation=None,
    ):
        score = 0
        reasons = []

        authorization_context = None
        policy_context = None

        # ---------------------------------------------------------
        # 1. ML ANOMALY
        # ---------------------------------------------------------
        if anomaly_result.get("is_anomaly"):
            anomaly_score = anomaly_result.get(
                "anomaly_score",
                0.0,
            )

            if anomaly_score >= 0.90:
                score += 35
                reasons.append(
                    "Behavior is highly anomalous compared with the employee baseline."
                )

            elif anomaly_score >= 0.70:
                score += 25
                reasons.append(
                    "Behavior significantly deviates from the employee baseline."
                )

            else:
                score += 15
                reasons.append(
                    "Behavior deviates from the employee baseline."
                )

        # ---------------------------------------------------------
        # 2. SENSITIVE DATA ACTIVITY
        # ---------------------------------------------------------
        sensitive_ratio = features.get(
            "sensitive_ratio_zscore",
            0.0,
        )

        sensitive_events = features.get(
            "sensitive_events_zscore",
            0.0,
        )

        if sensitive_ratio >= 5 or sensitive_events >= 5:
            score += 25
            reasons.append(
                "Sensitive-file activity is significantly higher than normal."
            )

        elif sensitive_ratio >= 2 or sensitive_events >= 2:
            score += 15
            reasons.append(
                "Sensitive-file activity is above normal."
            )

        # ---------------------------------------------------------
        # 3. DATA VOLUME
        # ---------------------------------------------------------
        data_volume = features.get(
            "data_volume_zscore",
            0.0,
        )

        if data_volume >= 5:
            score += 20
            reasons.append(
                "Data volume is significantly higher than the employee baseline."
            )

        elif data_volume >= 2:
            score += 10
            reasons.append(
                "Data volume is above the normal baseline."
            )

        # ---------------------------------------------------------
        # 4. ACTIVITY BURST
        # ---------------------------------------------------------
        activity_rate = features.get(
            "activity_rate_zscore",
            0.0,
        )

        if activity_rate >= 5:
            score += 10
            reasons.append(
                "Activity rate indicates an unusual behavioral burst."
            )

        elif activity_rate >= 2:
            score += 5
            reasons.append(
                "Activity rate is above normal."
            )

        # ---------------------------------------------------------
        # 5. AFTER-HOURS ACTIVITY
        # ---------------------------------------------------------
        if features.get("after_hours_deviation", 0) == 1:
            score += 10
            reasons.append(
                "Activity occurred outside the employee's normal working hours."
            )

        # ---------------------------------------------------------
        # 6. OBSERVED ACTIVITY
        # ---------------------------------------------------------
        observed_activity = self._parse_observed_activity(
            features.get("observed_activity", "")
        )

        activity_type = self._classify_observed_activity(
            observed_activity=observed_activity,
            features=features,
        )

        # ---------------------------------------------------------
        # 7. ROLE POLICY
        # ---------------------------------------------------------
        if policy_evaluation is not None:
            policy_context = {
                "violated": policy_evaluation.violated,
                "violations": policy_evaluation.violations,
                "matched_activities": policy_evaluation.matched_activities,
            }

            if policy_evaluation.violated:
                # Policy violations are strong evidence because they
                # represent deviation from explicit organizational rules.
                score += min(
                    30,
                    len(policy_evaluation.violations) * 10,
                )

                for violation in policy_evaluation.violations:
                    reasons.append(
                        f"Role-policy violation: {violation}"
                    )

        # ---------------------------------------------------------
        # 8. AUTHORIZATION
        # ---------------------------------------------------------
        if authorization is not None:

            allowed_activity = self._normalize_activity(
                authorization.allowed_activity
            )

            authorized_activities = {
                "delete": {"delete", "mass_deletion"},
                "modify": {"modify", "mass_modification"},
                "create": {"create", "mass_creation"},
                "move": {"move", "file_movement"},
            }

            scope_match = activity_type in authorized_activities.get(
                allowed_activity,
                {allowed_activity},
            )

            if scope_match:
                authorization_context = {
                    "exception_id": authorization.id,
                    "reason": authorization.reason,
                    "authorized_by": authorization.authorized_by,
                    "allowed_activity": authorization.allowed_activity,
                    "matched_activity": activity_type,
                    "scope_match": True,
                    "start_time": authorization.start_time,
                    "end_time": authorization.end_time,
                }

                score -= 30

                reasons.append(
                    "An active authorization exception explicitly covers "
                    "the observed activity type."
                )

            else:
                authorization_context = {
                    "exception_id": authorization.id,
                    "reason": authorization.reason,
                    "authorized_by": authorization.authorized_by,
                    "allowed_activity": authorization.allowed_activity,
                    "detected_activity": activity_type,
                    "observed_activity": sorted(observed_activity),
                    "scope_match": False,
                    "start_time": authorization.start_time,
                    "end_time": authorization.end_time,
                }

                reasons.append(
                    "An active authorization exception exists, "
                    "but it does not cover the observed activity."
                )

        # ---------------------------------------------------------
        # 9. BOUND SCORE
        # ---------------------------------------------------------
        score = max(
            0,
            min(score, 100),
        )

        # ---------------------------------------------------------
        # 10. RISK LEVEL
        # ---------------------------------------------------------
        if score >= 70:
            risk_level = "HIGH"

        elif score >= 40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        if not reasons:
            reasons.append(
                "No significant behavioral risk indicators detected."
            )

        return RiskResult(
            risk_score=score,
            risk_level=risk_level,
            reasons=reasons,
            authorization_context=authorization_context,
            policy_context=policy_context,
        )

    # =============================================================
    # ACTIVITY HELPERS
    # =============================================================

    @staticmethod
    def _parse_observed_activity(activity: str) -> set[str]:
        """
        Convert the stored comma-separated activity string into
        a normalized set.

        Example:
            "create,modify,move"

        becomes:
            {"create", "modify", "move"}
        """

        if not activity:
            return set()

        return {
            item.strip().lower()
            for item in activity.split(",")
            if item.strip()
        }

    @staticmethod
    def _normalize_activity(activity: str) -> str:
        """
        Normalize authorization activity names.
        """

        if not activity:
            return ""

        return (
            activity
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

    @classmethod
    def _classify_observed_activity(
        cls,
        observed_activity: set[str],
        features,
    ) -> str:
        """
        Determine the behavioral activity category using
        explicitly observed filesystem operations.

        This method does NOT invent file-read or transfer events.

        Supported categories:
        - mass_deletion
        - mass_modification
        - mass_creation
        - file_movement
        - general_file_activity
        """

        # ---------------------------------------------------------
        # 1. DELETE
        # ---------------------------------------------------------
        if (
            "delete" in observed_activity
            and features.get("files_deleted_zscore", 0.0) >= 5
        ):
            return "mass_deletion"

        # ---------------------------------------------------------
        # 2. MODIFY
        # ---------------------------------------------------------
        if (
            "modify" in observed_activity
            and features.get("files_modified_zscore", 0.0) >= 5
        ):
            return "mass_modification"

        # ---------------------------------------------------------
        # 3. CREATE
        # ---------------------------------------------------------
        if (
            "create" in observed_activity
            and features.get("files_created_zscore", 0.0) >= 5
        ):
            return "mass_creation"

        # ---------------------------------------------------------
        # 4. MOVE
        # ---------------------------------------------------------
        if (
            "move" in observed_activity
            and features.get("files_moved_zscore", 0.0) >= 5
        ):
            return "file_movement"

        # ---------------------------------------------------------
        # 5. GENERAL ACTIVITY
        # ---------------------------------------------------------
        return "general_file_activity"