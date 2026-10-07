from sqlmodel import Session, select

from app.detection.risk_engine import RiskEngine
from app.models.behavioral_baseline import BehavioralBaseline
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.models.employee import Employee
from app.models.role_policy import RolePolicy
from app.services.alert_service import create_alert_if_required
from app.services.exception_service import get_active_exception
from app.services.ml_inference import detect_behavioral_anomaly
from app.services.policy_evaluator import evaluate_window_against_policy


def process_behavioral_window(
    window: BehavioralWindow,
    session: Session,
):
    """
    Process one behavioral window through the complete
    insider-threat detection pipeline.

    Pipeline:

        Behavioral Window
              ↓
        Device / Employee
              ↓
        Role Policy Evaluation
              ↓
        Employee Behavioral Baseline
              ↓
        Isolation Forest
              ↓
        Exception / Authorization Context
              ↓
        Hybrid Risk Engine
              ↓
        Alert Creation
    """

    # ---------------------------------------------------------
    # 1. LOAD DEVICE
    # ---------------------------------------------------------
    device = session.get(
        Device,
        window.device_id,
    )

    if not device:
        raise ValueError(
            f"Device {window.device_id} not found."
        )

    # ---------------------------------------------------------
    # 2. LOAD EMPLOYEE
    # ---------------------------------------------------------
    employee = session.get(
        Employee,
        device.employee_id,
    )

    if not employee:
        raise ValueError(
            f"Employee {device.employee_id} not found."
        )

    # ---------------------------------------------------------
    # 3. LOAD ROLE POLICY
    # ---------------------------------------------------------
    policy = session.exec(
        select(RolePolicy).where(
            RolePolicy.role == employee.role,
            RolePolicy.is_active == True,
        )
    ).first()

    if not policy:
        return {
            "status": "SKIPPED",
            "reason": (
                f"No active role policy found for "
                f"role '{employee.role}'."
            ),
            "window_id": window.id,
            "employee_id": employee.id,
            "device_id": device.id,
            "role": employee.role,
            "alert": None,
        }

    # ---------------------------------------------------------
    # 4. EVALUATE WINDOW AGAINST ROLE POLICY
    # ---------------------------------------------------------
    policy_evaluation = evaluate_window_against_policy(
        window=window,
        policy=policy,
    )

    # ---------------------------------------------------------
    # 5. LOAD EMPLOYEE BASELINE
    # ---------------------------------------------------------
    baseline = session.exec(
        select(BehavioralBaseline).where(
            BehavioralBaseline.employee_id == device.employee_id
        )
    ).first()

    if not baseline:
        return {
            "status": "SKIPPED",
            "reason": (
                f"No behavioral baseline found for "
                f"employee {device.employee_id}."
            ),
            "window_id": window.id,
            "employee_id": device.employee_id,
            "device_id": device.id,
            "role": employee.role,
            "policy": {
                "policy_id": policy.id,
                "role": policy.role,
                "violated": policy_evaluation.violated,
                "violations": policy_evaluation.violations,
                "matched_activities": (
                    policy_evaluation.matched_activities
                ),
            },
            "alert": None,
        }

    # ---------------------------------------------------------
    # 6. RUN ML ANOMALY DETECTION
    # ---------------------------------------------------------
    try:
        anomaly_result = detect_behavioral_anomaly(
            window=window,
            baseline=baseline,
            session=session,
        )

    except ValueError as exc:
        return {
            "status": "SKIPPED",
            "reason": str(exc),
            "window_id": window.id,
            "employee_id": device.employee_id,
            "device_id": device.id,
            "role": employee.role,
            "policy": {
                "policy_id": policy.id,
                "role": policy.role,
                "violated": policy_evaluation.violated,
                "violations": policy_evaluation.violations,
                "matched_activities": (
                    policy_evaluation.matched_activities
                ),
            },
            "alert": None,
        }

    # ---------------------------------------------------------
    # 7. CHECK ACTIVE AUTHORIZATION EXCEPTION
    # ---------------------------------------------------------
    authorization = get_active_exception(
        employee_id=device.employee_id,
        activity_time=window.window_end,
        activity=window.observed_activity,
        session=session,
    )

    # ---------------------------------------------------------
    # 8. RUN HYBRID RISK ENGINE
    # ---------------------------------------------------------
    risk_engine = RiskEngine()

    risk_result = risk_engine.evaluate(
        anomaly_result=anomaly_result,
        features=anomaly_result["features"],
        authorization=authorization,
        policy_evaluation=policy_evaluation,
    )

    # ---------------------------------------------------------
    # 9. CREATE / UPDATE ALERT
    # ---------------------------------------------------------
    alert = create_alert_if_required(
        window=window,
        device=device,
        risk_result=risk_result,
        session=session,
    )

    # ---------------------------------------------------------
    # 10. RETURN PROCESSING RESULT
    # ---------------------------------------------------------
    return {
        "status": "ANALYZED",

        "window_id": window.id,

        "employee_id": anomaly_result["employee_id"],

        "device_id": anomaly_result["device_id"],

        "role": employee.role,

        "policy": {
            "policy_id": policy.id,
            "role": policy.role,
            "violated": policy_evaluation.violated,
            "violations": policy_evaluation.violations,
            "matched_activities": (
                policy_evaluation.matched_activities
            ),
        },

        "anomaly": {
            "is_anomaly": anomaly_result["is_anomaly"],
            "anomaly_score": anomaly_result["anomaly_score"],
            "raw_score": anomaly_result["raw_score"],
        },

        "risk": {
            "risk_score": risk_result.risk_score,
            "risk_level": risk_result.risk_level,
            "reasons": risk_result.reasons,
            "authorization_context": (
                risk_result.authorization_context
            ),
            "policy_context": (
                risk_result.policy_context
            ),
        },

        "alert": (
            {
                "id": alert.id,
                "status": alert.status,
                "risk_score": alert.risk_score,
                "risk_level": alert.risk_level,
            }
            if alert
            else None
        ),
    }