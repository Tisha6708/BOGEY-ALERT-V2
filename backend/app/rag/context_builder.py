from typing import Any


def build_threat_context(
    *,
    employee: dict[str, Any],
    window: dict[str, Any],
    anomaly: dict[str, Any],
    risk: dict[str, Any],
    policy: dict[str, Any] | None = None,
    authorization: dict[str, Any] | None = None,
) -> str:
    """
    Convert BOGEY-ALERT detection evidence into a structured
    natural-language context for RAG retrieval and threat explanation.
    """

    lines = []

    # ---------------------------------------------------------
    # EMPLOYEE CONTEXT
    # ---------------------------------------------------------

    role = employee.get("role", "unknown")
    department = employee.get("department", "unknown")

    lines.append(
        f"Employee role: {role}. Department: {department}."
    )

    # ---------------------------------------------------------
    # OBSERVED ACTIVITY
    # ---------------------------------------------------------

    observed_activity = window.get(
        "observed_activity",
        "unknown",
    )

    lines.append(
        f"Observed filesystem activity: {observed_activity}."
    )

    # ---------------------------------------------------------
    # BEHAVIORAL EVIDENCE
    # ---------------------------------------------------------

    lines.append(
        f"Total events: {window.get('total_events', 0)}."
    )

    lines.append(
        f"Files created: {window.get('files_created', 0)}."
    )

    lines.append(
        f"Files modified: {window.get('files_modified', 0)}."
    )

    lines.append(
        f"Files deleted: {window.get('files_deleted', 0)}."
    )

    lines.append(
        f"Files moved: {window.get('files_moved', 0)}."
    )

    lines.append(
        f"Sensitive events: {window.get('sensitive_events', 0)}."
    )

    lines.append(
        f"Sensitive activity ratio: "
        f"{window.get('sensitive_ratio', 0.0):.2f}."
    )

    lines.append(
        f"Total data volume: "
        f"{window.get('total_data_volume', 0)} bytes."
    )

    lines.append(
        f"Activity rate: "
        f"{window.get('activity_rate', 0.0):.2f}."
    )

    lines.append(
        f"After-hours activity: "
        f"{window.get('after_hours', False)}."
    )

    # ---------------------------------------------------------
    # ML EVIDENCE
    # ---------------------------------------------------------

    anomaly_score = anomaly.get(
        "anomaly_score",
        0.0,
    )

    is_anomaly = anomaly.get(
        "is_anomaly",
        False,
    )

    lines.append(
        f"Machine-learning anomaly detection: "
        f"{'ANOMALOUS' if is_anomaly else 'NORMAL'}."
    )

    lines.append(
        f"ML anomaly score: {anomaly_score:.4f}."
    )

    # ---------------------------------------------------------
    # RISK EVIDENCE
    # ---------------------------------------------------------

    lines.append(
        f"Risk score: {risk.get('risk_score', 0)}."
    )

    lines.append(
        f"Risk level: {risk.get('risk_level', 'UNKNOWN')}."
    )

    reasons = risk.get("reasons", [])

    if reasons:
        lines.append(
            "Risk indicators: "
            + "; ".join(str(reason) for reason in reasons)
            + "."
        )

    # ---------------------------------------------------------
    # POLICY EVIDENCE
    # ---------------------------------------------------------

    if policy:
        violations = policy.get(
            "violations",
            [],
        )

        if violations:
            lines.append(
                "Role-policy violations: "
                + "; ".join(
                    str(violation)
                    for violation in violations
                )
                + "."
            )

    # ---------------------------------------------------------
    # AUTHORIZATION EVIDENCE
    # ---------------------------------------------------------

    if authorization:
        allowed_activity = authorization.get(
            "allowed_activity",
            "unknown",
        )

        scope_match = authorization.get(
            "scope_match",
            False,
        )

        lines.append(
            "Authorization context: "
            f"An active authorization exception exists for "
            f"{allowed_activity} activity."
        )

        lines.append(
            f"Authorization observed activity: "
            f"{observed_activity}."
        )

        lines.append(
            f"Authorization allowed activity: "
            f"{allowed_activity}."
        )

        lines.append(
            f"Authorization scope match: "
            f"{scope_match}."
        )

        # -----------------------------------------------------
        # DETERMINISTIC AUTHORIZATION CONCLUSION
        # -----------------------------------------------------

        if scope_match:
            lines.append(
                "AUTHORIZATION CONCLUSION: "
                f"The observed '{observed_activity}' activity is "
                "AUTHORIZED by the active exception because the "
                "authorization scope matches."
            )

            lines.append(
                "SENSITIVE DATA AUTHORIZATION STATUS: UNKNOWN. "
                "The supplied evidence does not establish whether "
                "the active authorization specifically covers the "
                "sensitive data involved."
            )

        else:
            lines.append(
                "AUTHORIZATION CONCLUSION: "
                f"The observed '{observed_activity}' activity is "
                "NOT COVERED by the supplied authorization exception."
            )

    else:
        lines.append(
            "Authorization context: No active authorization "
            "exception was identified."
        )

        lines.append(
            "AUTHORIZATION CONCLUSION: "
            f"No authorization evidence was found for the observed "
            f"'{observed_activity}' activity."
        )

        lines.append(
            "SENSITIVE DATA AUTHORIZATION STATUS: UNKNOWN. "
            "No authorization evidence was supplied that establishes "
            "whether sensitive data activity was authorized."
        )

    # ---------------------------------------------------------
    # FINAL ANALYST INTERPRETATION RULE
    # ---------------------------------------------------------

    lines.append(
        "ANALYST INTERPRETATION RULE: "
        "Keep ML anomaly, role-policy compliance, and authorization "
        "as separate concepts. Do not treat a role-policy violation "
        "as proof that an explicitly matched authorization exception "
        "is invalid."
    )

    return "\n".join(lines)