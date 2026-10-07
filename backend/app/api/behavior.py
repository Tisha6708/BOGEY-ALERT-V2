from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.security import get_authenticated_device
from app.db.session import get_session
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.schemas.behavioral_window import (
    BehavioralWindowCreate,
    BehavioralWindowRead,
)
from app.services.window_processor import process_behavioral_window


router = APIRouter(
    prefix="/behavior",
    tags=["Behavioral Windows"],
)


def process_window_in_background(
    window_id: int,
):
    """
    Process a persisted behavioral window outside
    the HTTP request lifecycle.

    A new database session is created because the
    original request session must not be reused by
    the background task.
    """

    from app.db.session import get_session

    session_generator = get_session()
    session = next(session_generator)

    try:
        window = session.get(
            BehavioralWindow,
            window_id,
        )

        if not window:
            print(
                f"[DETECTION] Behavioral window "
                f"{window_id} no longer exists."
            )
            return

        result = process_behavioral_window(
            window=window,
            session=session,
        )

        print(
            f"[DETECTION] Window {window_id}: "
            f"{result.get('status')}"
        )

        if result.get("status") == "ANALYZED":
            risk = result.get("risk", {})

            print(
                f"[DETECTION] Risk: "
                f"{risk.get('risk_score')} "
                f"({risk.get('risk_level')})"
            )

            alert = result.get("alert")

            if alert:
                print(
                    f"[ALERT] Alert {alert['id']} "
                    f"created/updated: "
                    f"{alert['risk_level']}"
                )

    except Exception as exc:
        # Detection failure must not invalidate telemetry
        # that was already successfully persisted.
        print(
            f"[DETECTION ERROR] "
            f"Window {window_id}: {exc}"
        )

    finally:
        try:
            session.close()
        except Exception:
            pass


@router.get(
    "/windows",
    response_model=list[BehavioralWindowRead],
)
def get_behavioral_windows(
    device_id: int | None = Query(
        default=None,
        description="Filter behavioral windows by device.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    session: Session = Depends(get_session),
):
    statement = select(BehavioralWindow).order_by(
        BehavioralWindow.window_start.desc()
    )

    if device_id is not None:
        statement = statement.where(
            BehavioralWindow.device_id == device_id
        )

    statement = statement.limit(limit)

    windows = session.exec(statement).all()

    return list(windows)


@router.get(
    "/windows/{window_id}",
    response_model=BehavioralWindowRead,
)
def get_behavioral_window(
    window_id: int,
    session: Session = Depends(get_session),
):
    window = session.get(
        BehavioralWindow,
        window_id,
    )

    if not window:
        raise HTTPException(
            status_code=404,
            detail="Behavioral window not found.",
        )

    return window


@router.post(
    "/windows",
    response_model=BehavioralWindowRead,
    status_code=201,
)
def create_behavioral_window(
    window_data: BehavioralWindowCreate,
    background_tasks: BackgroundTasks,
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    # ---------------------------------------------------------
    # 1. TIME VALIDATION
    # ---------------------------------------------------------
    if window_data.window_end <= window_data.window_start:
        raise HTTPException(
            status_code=400,
            detail="window_end must be later than window_start.",
        )

    # ---------------------------------------------------------
    # 2. EVENT COUNT CONSISTENCY
    # ---------------------------------------------------------
    operation_total = (
        window_data.files_created
        + window_data.files_modified
        + window_data.files_deleted
        + window_data.files_moved
    )

    if operation_total > window_data.total_events:
        raise HTTPException(
            status_code=400,
            detail=(
                "The sum of files_created, files_modified, "
                "files_deleted, and files_moved cannot exceed "
                "total_events."
            ),
        )

    # ---------------------------------------------------------
    # 3. SENSITIVE EVENT CONSISTENCY
    # ---------------------------------------------------------
    if window_data.sensitive_events > window_data.total_events:
        raise HTTPException(
            status_code=400,
            detail="sensitive_events cannot exceed total_events.",
        )

    # ---------------------------------------------------------
    # 4. SENSITIVE RATIO CONSISTENCY
    # ---------------------------------------------------------
    if window_data.total_events == 0:
        if window_data.sensitive_ratio != 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "sensitive_ratio must be 0 when "
                    "total_events is 0."
                ),
            )
    else:
        expected_ratio = (
            window_data.sensitive_events
            / window_data.total_events
        )

        if abs(
            window_data.sensitive_ratio - expected_ratio
        ) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=(
                    "sensitive_ratio is inconsistent with "
                    "sensitive_events / total_events."
                ),
            )

    # ---------------------------------------------------------
    # 5. CREATE BEHAVIORAL WINDOW
    # ---------------------------------------------------------
    window = BehavioralWindow(
        device_id=device.id,
        window_start=window_data.window_start,
        window_end=window_data.window_end,
        observed_activity=window_data.observed_activity,
        total_events=window_data.total_events,
        files_created=window_data.files_created,
        files_modified=window_data.files_modified,
        files_deleted=window_data.files_deleted,
        files_moved=window_data.files_moved,
        sensitive_events=window_data.sensitive_events,
        sensitive_ratio=window_data.sensitive_ratio,
        total_data_volume=window_data.total_data_volume,
        unique_extensions=window_data.unique_extensions,
        directory_breadth=window_data.directory_breadth,
        activity_rate=window_data.activity_rate,
        after_hours=window_data.after_hours,
        session_id=window_data.session_id,
    )

    session.add(window)
    session.commit()
    session.refresh(window)

    # ---------------------------------------------------------
    # 6. START BACKGROUND ANALYSIS
    # ---------------------------------------------------------
    background_tasks.add_task(
        process_window_in_background,
        window.id,
    )

    # ---------------------------------------------------------
    # 7. RETURN PERSISTED TELEMETRY
    # ---------------------------------------------------------
    return window