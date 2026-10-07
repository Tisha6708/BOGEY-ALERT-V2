from datetime import datetime, timedelta, timezone

import requests


BACKEND_URL = "http://127.0.0.1:8000"
BEHAVIOR_ENDPOINT = f"{BACKEND_URL}/behavior/windows"

# Credential for DEVICE-004
DEVICE_CREDENTIAL = "bJ4Je-YR_1Dew1fsYRHGiZmFpZZEfgknWbm3Ux74z3E"


def main():
    end_time = datetime(2026, 10, 5, 5, 0, tzinfo=timezone.utc)
    start_time = end_time - timedelta(minutes=1)

    payload = {
        "window_start": start_time.isoformat(),
        "window_end": end_time.isoformat(),

        # Developer policy allows create/modify/move,
        # so DELETE should trigger a policy violation.
        "observed_activity": "delete",

        # Deliberately abnormal volume.
        "total_events": 120,
        "files_created": 0,
        "files_modified": 10,
        "files_deleted": 110,
        "files_moved": 0,

        # Deliberately suspicious sensitive activity.
        "sensitive_events": 80,
        "sensitive_ratio": 80 / 120,

        # Very large compared with the normal baseline.
        "total_data_volume": 524288000,

        "unique_extensions": 15,
        "directory_breadth": 20,
        "activity_rate": 2.0,

        # Preliminary ML feature.
        "after_hours": True,

        "session_id": "suspicious-test-session",
    }

    headers = {
        "Authorization": f"Bearer {DEVICE_CREDENTIAL}",
        "Content-Type": "application/json",
        "User-Agent": "BOGEY-ALERT-SuspiciousTest/1.0",
    }

    print("=" * 60)
    print("BOGEY-ALERT SUSPICIOUS WINDOW TEST")
    print("=" * 60)

    try:
        response = requests.post(
            BEHAVIOR_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=30,
        )

        print(f"HTTP Status: {response.status_code}")
        print("Response:")
        print(response.text)

    except requests.RequestException as exc:
        print(f"NETWORK ERROR: {exc}")


if __name__ == "__main__":
    main()