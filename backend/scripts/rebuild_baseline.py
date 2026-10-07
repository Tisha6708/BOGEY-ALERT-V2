from sqlmodel import Session

from app.db.session import engine
from app.services.baseline import calculate_baseline


EMPLOYEE_ID = 1
BASELINE_SESSION_ID = "realistic-baseline-training"


def main():
    print("=" * 60)
    print("BOGEY-ALERT BASELINE REBUILD")
    print("=" * 60)

    with Session(engine) as session:

        baseline = calculate_baseline(
            employee_id=EMPLOYEE_ID,
            session=session,
            session_id=BASELINE_SESSION_ID,
        )

        print(
            f"Employee       : {baseline.employee_id}"
        )

        print(
            f"Samples        : {baseline.sample_count}"
        )

        print(
            f"Avg events     : "
            f"{baseline.avg_events_per_window:.2f}"
        )

        print(
            f"Avg data volume: "
            f"{baseline.avg_data_volume:.2f}"
        )

        print(
            f"Avg activity   : "
            f"{baseline.avg_activity_rate:.4f}"
        )

        print(
            f"After-hours    : "
            f"{baseline.after_hours_ratio:.4f}"
        )

    print("=" * 60)
    print("BASELINE REBUILT SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()