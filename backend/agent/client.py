import time

import requests

from agent.config import (
    AGENT_VERSION,
    DEVICE_CREDENTIAL,
)


class BackendClient:
    """
    Handles authenticated communication between the
    endpoint agent and BOGEY-ALERT backend.
    """

    def __init__(
        self,
        behavior_endpoint: str,
        device_credential: str = DEVICE_CREDENTIAL,
    ):
        self.behavior_endpoint = behavior_endpoint
        self.device_credential = device_credential

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": (
                    f"Bearer {self.device_credential}"
                ),
                "User-Agent": (
                    f"BOGEY-ALERT-Agent/{AGENT_VERSION}"
                ),
                "Content-Type": "application/json",
            }
        )

    def validate_configuration(self) -> None:
        if not self.device_credential:
            raise ValueError(
                "BOGEY_DEVICE_CREDENTIAL is not configured."
            )

    def send_behavioral_window(
        self,
        features: dict,
        retries: int = 3,
    ) -> bool:
        """
        Send one aggregated behavioral window
        to the backend.
        """

        self.validate_configuration()

        if not features.get("window_start"):
            return False

        payload = {
            "window_start": features[
                "window_start"
            ].isoformat(),

            "window_end": features[
                "window_end"
            ].isoformat(),

            # -------------------------------------------------
            # OBSERVED ACTIVITY
            # -------------------------------------------------
            "observed_activity": features.get(
                "observed_activity",
                "",
            ),

            # -------------------------------------------------
            # EVENT COUNTS
            # -------------------------------------------------
            "total_events": features[
                "total_events"
            ],

            "files_created": features[
                "files_created"
            ],

            "files_modified": features[
                "files_modified"
            ],

            "files_deleted": features[
                "files_deleted"
            ],

            "files_moved": features[
                "files_moved"
            ],

            # -------------------------------------------------
            # SENSITIVE DATA
            # -------------------------------------------------
            "sensitive_events": features[
                "sensitive_events"
            ],

            "sensitive_ratio": features[
                "sensitive_ratio"
            ],

            # -------------------------------------------------
            # VOLUME / DIVERSITY
            # -------------------------------------------------
            "total_data_volume": features[
                "total_data_volume"
            ],

            "unique_extensions": features[
                "unique_extensions"
            ],

            "directory_breadth": features[
                "directory_breadth"
            ],

            # -------------------------------------------------
            # BEHAVIOR
            # -------------------------------------------------
            "activity_rate": features[
                "activity_rate"
            ],

            "after_hours": features[
                "after_hours"
            ],

            "session_id": features.get(
                "session_id"
            ),
        }

        for attempt in range(
            1,
            retries + 1,
        ):

            try:

                response = self.session.post(
                    self.behavior_endpoint,
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 201:
                    return True

                if response.status_code in {
                    401,
                    403,
                }:
                    print(
                        "[AUTH ERROR] "
                        "Agent authentication failed."
                    )
                    return False

                print(
                    f"[BACKEND ERROR] "
                    f"HTTP {response.status_code}: "
                    f"{response.text}"
                )

            except requests.RequestException as exc:

                print(
                    f"[NETWORK ERROR] "
                    f"Attempt {attempt}/{retries}: "
                    f"{exc}"
                )

            if attempt < retries:
                time.sleep(
                    2 ** (attempt - 1)
                )

        return False