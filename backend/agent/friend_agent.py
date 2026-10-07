import signal
import sys
import time
import uuid
from datetime import datetime, timezone

from agent.classifier import SensitiveFileClassifier
from agent.client import BackendClient
from agent.config import (
    BEHAVIOR_ENDPOINT,
    MONITORED_DIRECTORIES,
    SEND_INTERVAL_SECONDS,
)
from agent.feature_buffer import FeatureBuffer
from agent.monitor import FileSystemMonitor


class BogeyAgent:
    """
    BOGEY-ALERT v2.0 endpoint agent.

    Responsibilities:
        - Filesystem monitoring
        - Local sensitivity classification
        - Behavioral aggregation
        - Privacy-safe telemetry transmission

    The agent does NOT:
        - calculate threat risk
        - make security decisions
        - block employees
        - upload file contents
        - upload complete filesystem paths
    """

    def __init__(self):

        self.running = True

        self.session_id = str(
            uuid.uuid4()
        )

        self.classifier = (
            SensitiveFileClassifier()
        )

        self.feature_buffer = FeatureBuffer()

        self.backend_client = BackendClient(
            behavior_endpoint=BEHAVIOR_ENDPOINT
        )

        self.monitor = FileSystemMonitor(
            directories=MONITORED_DIRECTORIES,
            event_callback=self.handle_event,
            classifier=self.classifier,
        )

    def handle_event(
        self,
        event: dict,
    ):
        """
        Receive normalized filesystem activity
        from the filesystem monitor.
        """

        event["session_id"] = (
            self.session_id
        )

        self.feature_buffer.add_event(
            event_type=event["event_type"],
            file_extension=event.get(
                "file_extension"
            ),
            file_size=event.get(
                "file_size",
                0,
            ),
            is_sensitive=event.get(
                "is_sensitive",
                False,
            ),
            directory_type=event.get(
                "directory_type",
                "unknown",
            ),
            session_id=self.session_id,
            timestamp=event.get(
                "timestamp"
            ),
        )

        print(
            f"[EVENT] "
            f"{event['event_type']} | "
            f"{event.get('file_extension')} | "
            f"{event.get('directory_type')} | "
            f"sensitive="
            f"{event.get('is_sensitive')}"
        )

    def send_behavioral_window(self):
        """
        Close the current collection interval,
        build the behavioral window, and send it
        to the backend.

        The buffer is cleared only after a
        successful backend submission.
        """

        # ---------------------------------------------------------
        # 1. MARK END OF COLLECTION INTERVAL
        # ---------------------------------------------------------
        window_end = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # 2. BUILD BEHAVIORAL WINDOW
        # ---------------------------------------------------------
        features = (
            self.feature_buffer.build_window(
                window_end=window_end
            )
        )

        if features is None:
            return

        print(
            "[FEATURE WINDOW]",
            features,
        )

        # ---------------------------------------------------------
        # 3. SEND TO BACKEND
        # ---------------------------------------------------------
        success = (
            self.backend_client
            .send_behavioral_window(
                features
            )
        )

        # ---------------------------------------------------------
        # 4. RESET ONLY AFTER SUCCESS
        # ---------------------------------------------------------
        if success:

            print(
                "[BACKEND] "
                "Behavioral window accepted."
            )

            print(
                "[BACKEND] "
                f"Observed activity: "
                f"{features['observed_activity']}"
            )

            self.feature_buffer.reset(
                window_start=window_end
            )

        else:

            print(
                "[BACKEND] "
                "Behavioral window was not accepted."
            )

    def start(self):

        print("=" * 60)

        print(
            "BOGEY-ALERT v2.0 "
            "ENDPOINT AGENT"
        )

        print("=" * 60)

        print(
            f"[AGENT] Session: "
            f"{self.session_id}"
        )

        print(
            "[AGENT] Monitoring:"
        )

        for directory in (
            MONITORED_DIRECTORIES
        ):
            print(
                f"         {directory}"
            )

        self.backend_client.validate_configuration()

        self.monitor.start()

        print(
            "[AGENT] Agent is running."
        )

        try:

            while self.running:

                self.send_behavioral_window()

                time.sleep(
                    SEND_INTERVAL_SECONDS
                )

        except KeyboardInterrupt:

            self.stop()

    def stop(self):

        if not self.running:
            return

        print(
            "\n[AGENT] "
            "Shutting down..."
        )

        self.running = False

        self.monitor.stop()

        print(
            "[AGENT] "
            "Shutdown complete."
        )


agent = BogeyAgent()


def handle_shutdown_signal(
    signum,
    frame,
):
    agent.stop()
    sys.exit(0)


signal.signal(
    signal.SIGINT,
    handle_shutdown_signal,
)

signal.signal(
    signal.SIGTERM,
    handle_shutdown_signal,
)


if __name__ == "__main__":
    agent.start()