import random
import time
from datetime import datetime, timedelta, timezone

import requests


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8000"

BEHAVIOR_ENDPOINT = (
    f"{BACKEND_URL}/behavior/windows"
)

DEVICE_CREDENTIAL = (
    "bJ4Je-YR_1Dew1fsYRHGiZmFpZZEfgknWbm3Ux74z3E"
)

NUMBER_OF_WINDOWS = 30

random.seed(42)


# ============================================================
# NORMAL DEVELOPER BEHAVIOR
# ============================================================

def generate_normal_window(index: int) -> dict:

    # Realistic developer activity.
    total_events = random.randint(15, 60)

    files_created = random.randint(1, 10)

    files_modified = random.randint(5, 35)

    files_deleted = random.randint(0, 3)

    files_moved = random.randint(0, 5)

    sensitive_events = random.choice(
        [0, 0, 0, 1]
    )

    total_data_volume = random.randint(
        10_000,
        80_000_000,
    )

    unique_extensions = random.randint(
        2,
        8,
    )

    directory_breadth = random.randint(
        1,
        8,
    )

    session_duration = random.randint(
        30,
        180,
    )

    # Make sure the event count is at least the
    # number of file operations.
    operation_count = (
        files_created
        + files_modified
        + files_deleted
        + files_moved
    )

    total_events = max(
        total_events,
        operation_count,
    )

    activity_rate = (
        total_events
        / session_duration
    )

    sensitive_ratio = (
        sensitive_events
        / max(total_events, 1)
    )

    observed_activity = []

    if files_created > 0:
        observed_activity.append("create")

    if files_modified > 0:
        observed_activity.append("modify")

    if files_deleted > 0:
        observed_activity.append("delete")

    if files_moved > 0:
        observed_activity.append("move")

    # Generate timestamps in working hours:
    # 09:00–18:00 IST = 03:30–12:30 UTC.
    #
    # We generate each window on a different historical
    # weekday so the baseline is not accidentally treated
    # as weekend/after-hours activity.

    base_date = (
        datetime.now(timezone.utc)
        - timedelta(days=40 - index)
    )

    # Force weekday.
    while base_date.weekday() >= 5:
        base_date += timedelta(days=1)

    start_time = base_date.replace(
        hour=random.randint(4, 12),
        minute=random.randint(0, 59),
        second=0,
        microsecond=0,
    )

    end_time = (
        start_time
        + timedelta(minutes=10)
    )

    return {
        "window_start": start_time.isoformat(),

        "window_end": end_time.isoformat(),

        "observed_activity": ",".join(
            observed_activity
        ),

        "total_events": total_events,

        "files_created": files_created,

        "files_modified": files_modified,

        "files_deleted": files_deleted,

        "files_moved": files_moved,

        "sensitive_events": sensitive_events,

        "sensitive_ratio": round(
            sensitive_ratio,
            4,
        ),

        "total_data_volume": total_data_volume,

        "unique_extensions": unique_extensions,

        "directory_breadth": directory_breadth,

        "activity_rate": round(
            activity_rate,
            4,
        ),

        "after_hours": False,

        "session_id": (
            "realistic-baseline-training"
        ),
    }


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "Authorization": (
            f"Bearer {DEVICE_CREDENTIAL}"
        ),
        "Content-Type": "application/json",
        "User-Agent": (
            "BOGEY-ALERT-BaselineGenerator/2.0"
        ),
    }
)


# ============================================================
# SEND WINDOWS
# ============================================================

def main():

    print("=" * 60)
    print("BOGEY-ALERT REALISTIC BASELINE GENERATOR")
    print("=" * 60)

    print(
        f"[BASELINE] Generating "
        f"{NUMBER_OF_WINDOWS} realistic normal windows..."
    )

    successful = 0

    for index in range(NUMBER_OF_WINDOWS):

        payload = generate_normal_window(
            index
        )

        try:

            response = session.post(
                BEHAVIOR_ENDPOINT,
                json=payload,
                timeout=10,
            )

            if response.status_code == 201:

                successful += 1

                print(
                    f"[{index + 1:02d}/"
                    f"{NUMBER_OF_WINDOWS}] "
                    f"Accepted | "
                    f"events="
                    f"{payload['total_events']} | "
                    f"modified="
                    f"{payload['files_modified']} | "
                    f"volume="
                    f"{payload['total_data_volume']}"
                )

            else:

                print(
                    f"[{index + 1:02d}/"
                    f"{NUMBER_OF_WINDOWS}] "
                    f"FAILED | "
                    f"HTTP "
                    f"{response.status_code} | "
                    f"{response.text}"
                )

        except requests.RequestException as exc:

            print(
                f"[{index + 1:02d}/"
                f"{NUMBER_OF_WINDOWS}] "
                f"NETWORK ERROR: {exc}"
            )

        time.sleep(0.15)

    print()
    print("=" * 60)

    print(
        f"[BASELINE] Successfully submitted: "
        f"{successful}/{NUMBER_OF_WINDOWS}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()