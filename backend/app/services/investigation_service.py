from sqlmodel import Session, select

from app.models.alert import Alert
from app.models.behavioral_baseline import BehavioralBaseline
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.models.employee import Employee
from app.models.role_policy import RolePolicy
from app.services.exception_service import get_active_exception
from app.services.ml_inference import detect_behavioral_anomaly
from app.services.policy_evaluator import evaluate_window_against_policy
from app.rag.service import RAGThreatAnalyzer


def get_alert_investigation(
    *,
    alert_id: int,
    session: Session,
) -> dict | None:

    # ---------------------------------------------------------
    # 1. LOAD ALERT
    # ---------------------------------------------------------
    alert = session.get(Alert, alert_id)

    if not alert:
        return None

    # ---------------------------------------------------------
    # 2. LOAD BEHAVIORAL WINDOW
    # ---------------------------------------------------------
    window = session.get(
        BehavioralWindow,
        alert.behavioral_window_id,
    )

    if not window:
        raise ValueError(
            f"Behavioral window {alert.behavioral_window_id} "
            "not found."
        )

    # ---------------------------------------------------------
    # 3. LOAD DEVICE
    # ---------------------------------------------------------
    device = session.get(
        Device,
        alert.device_id,
    )

    if not device:
        raise ValueError(
            f"Device {alert.device_id} not found."
        )

    # ---------------------------------------------------------
    # 4. LOAD EMPLOYEE
    # ---------------------------------------------------------
    employee = session.get(
        Employee,
        alert.employee_id,
    )

    if not employee:
        raise ValueError(
            f"Employee {alert.employee_id} not found."
        )

    # ---------------------------------------------------------
    # 5. LOAD ROLE POLICY
    # ---------------------------------------------------------
    policy = session.exec(
        select(RolePolicy).where(
            RolePolicy.role == employee.role,
            RolePolicy.is_active == True,
        )
    ).first()

    policy_context = None

    if policy:
        policy_evaluation = evaluate_window_against_policy(
            window=window,
            policy=policy,
        )

        policy_context = {
            "policy_id": policy.id,
            "role": policy.role,
            "description": policy.description,
            "violated": policy_evaluation.violated,
            "violations": policy_evaluation.violations,
            "matched_activities": (
                policy_evaluation.matched_activities
            ),
        }

    # ---------------------------------------------------------
    # 6. LOAD BASELINE
    # ---------------------------------------------------------
    baseline = session.exec(
        select(BehavioralBaseline).where(
            BehavioralBaseline.employee_id == employee.id
        )
    ).first()

    anomaly_result = None

    if baseline:
        anomaly_result = detect_behavioral_anomaly(
            window=window,
            baseline=baseline,
            session=session,
        )

    # ---------------------------------------------------------
    # 7. LOAD AUTHORIZATION CONTEXT
    # ---------------------------------------------------------
    authorization = get_active_exception(
        employee_id=employee.id,
        activity_time=window.window_end,
        activity=window.observed_activity,
        session=session,
    )

    authorization_context = None

    if authorization:
        authorization_context = {
            "exception_id": authorization.id,
            "reason": authorization.reason,
            "authorized_by": authorization.authorized_by,
            "allowed_activity": authorization.allowed_activity,
            "observed_activity": window.observed_activity,
            "scope_match": True,
            "status": authorization.status,
            "start_time": authorization.start_time,
            "end_time": authorization.end_time,
        }

    # ---------------------------------------------------------
    # 8. RECONSTRUCT RISK CONTEXT FROM STORED ALERT
    # ---------------------------------------------------------
    reasons = []

    if alert.reasons_json:
        import json

        try:
            reasons = json.loads(alert.reasons_json)
        except (json.JSONDecodeError, TypeError):
            reasons = [alert.reasons_json]

    risk_context = {
        "risk_score": alert.risk_score,
        "risk_level": alert.risk_level,
        "reasons": reasons,
        "authorization_context": (
            authorization_context
        ),
        "policy_context": policy_context,
    }

    # ---------------------------------------------------------
    # 9. BUILD RAG INPUT
    # ---------------------------------------------------------
    employee_data = {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "role": employee.role,
        "department": employee.department,
    }

    window_data = {
        "id": window.id,
        "observed_activity": window.observed_activity,
        "total_events": window.total_events,
        "files_created": window.files_created,
        "files_modified": window.files_modified,
        "files_deleted": window.files_deleted,
        "files_moved": window.files_moved,
        "sensitive_events": window.sensitive_events,
        "sensitive_ratio": window.sensitive_ratio,
        "total_data_volume": window.total_data_volume,
        "unique_extensions": window.unique_extensions,
        "directory_breadth": window.directory_breadth,
        "activity_rate": window.activity_rate,
        "after_hours": window.after_hours,
    }

    anomaly_data = (
        {
            "is_anomaly": anomaly_result["is_anomaly"],
            "anomaly_score": anomaly_result["anomaly_score"],
            "raw_score": anomaly_result["raw_score"],
        }
        if anomaly_result
        else {
            "is_anomaly": False,
            "anomaly_score": 0,
            "raw_score": 0,
        }
    )

    # ---------------------------------------------------------
    # 10. RUN RAG + GROQ
    # ---------------------------------------------------------
    rag_analyzer = RAGThreatAnalyzer()

    rag_result = rag_analyzer.analyze(
        employee=employee_data,
        window=window_data,
        anomaly=anomaly_data,
        risk=risk_context,
        policy=policy_context,
        authorization=authorization_context,
        top_k=4,
    )

    # ---------------------------------------------------------
    # 11. RETURN COMPLETE INVESTIGATION
    # ---------------------------------------------------------
    return {
        "alert": {
            "id": alert.id,
            "status": alert.status,
            "risk_score": alert.risk_score,
            "risk_level": alert.risk_level,
            "created_at": alert.created_at,
            "reviewed_at": alert.reviewed_at,
            "analyst_decision": alert.analyst_decision,
            "analyst_notes": alert.analyst_notes,
        },

        "employee": employee_data,

        "device": {
            "id": device.id,
            "device_code": device.device_code,
            "operating_system": device.operating_system,
            "agent_version": device.agent_version,
        },

        "window": window_data,

        "anomaly": anomaly_data,

        "risk": risk_context,

        "policy": policy_context,

        "authorization": authorization_context,

        "rag": {
            "policy_count": rag_result["policy_count"],
            "retrieved_policies": rag_result[
                "retrieved_policies"
            ],
            "threat_explanation": rag_result[
                "threat_explanation"
            ],
        },
    }