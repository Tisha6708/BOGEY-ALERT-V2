from datetime import datetime, timezone
from zoneinfo import ZoneInfo


POLICY_TIMEZONE = ZoneInfo("Asia/Kolkata")


class FeatureBuffer:
    """
    Aggregates endpoint filesystem events into behavioral windows.

    A behavioral window represents a collection interval, not merely
    the time between the first and last filesystem event.

    The endpoint collects minimal behavioral telemetry locally and
    sends aggregated features to the backend.
    """

    def __init__(self):
        self.reset()

    def reset(self, window_start: datetime | None = None):
        # ---------------------------------------------------------
        # EVENT COUNTS
        # ---------------------------------------------------------
        self.total_events = 0

        self.files_created = 0
        self.files_modified = 0
        self.files_deleted = 0
        self.files_moved = 0

        # ---------------------------------------------------------
        # SENSITIVE ACTIVITY
        # ---------------------------------------------------------
        self.sensitive_events = 0

        # ---------------------------------------------------------
        # DATA VOLUME
        # ---------------------------------------------------------
        self.total_data_volume = 0

        # ---------------------------------------------------------
        # DIVERSITY
        # ---------------------------------------------------------
        self.extensions = set()
        self.directories = set()

        # ---------------------------------------------------------
        # OBSERVED ACTIVITY TYPES
        # ---------------------------------------------------------
        self.observed_activities = set()

        # ---------------------------------------------------------
        # WINDOW TIMING
        # ---------------------------------------------------------
        self.window_start = self._normalize_timestamp(
            window_start
        )

        self.session_id = None

    def add_event(
        self,
        event_type: str,
        file_extension: str | None = None,
        file_size: int = 0,
        is_sensitive: bool = False,
        directory_type: str = "unknown",
        session_id: str | None = None,
        timestamp: datetime | None = None,
    ):
        """
        Add one filesystem event to the current behavioral window.

        Event timestamps are stored/handled in UTC, while policy-time
        calculations such as working hours are evaluated in the
        organization's configured policy timezone.
        """

        timestamp = self._normalize_timestamp(timestamp)

        # ---------------------------------------------------------
        # INITIALIZE COLLECTION WINDOW
        # ---------------------------------------------------------
        if self.window_start is None:
            self.window_start = timestamp

        if session_id:
            self.session_id = session_id

        event_type = event_type.strip().lower()

        # ---------------------------------------------------------
        # TOTAL EVENTS
        # ---------------------------------------------------------
        self.total_events += 1

        # ---------------------------------------------------------
        # EVENT TYPE
        # ---------------------------------------------------------
        if event_type == "create":
            self.files_created += 1
            self.observed_activities.add("create")

        elif event_type == "modify":
            self.files_modified += 1
            self.observed_activities.add("modify")

        elif event_type == "delete":
            self.files_deleted += 1
            self.observed_activities.add("delete")

        elif event_type == "move":
            self.files_moved += 1
            self.observed_activities.add("move")

        # ---------------------------------------------------------
        # SENSITIVE ACTIVITY
        # ---------------------------------------------------------
        if is_sensitive:
            self.sensitive_events += 1

        # ---------------------------------------------------------
        # DATA VOLUME
        # ---------------------------------------------------------
        if file_size > 0:
            self.total_data_volume += file_size

        # ---------------------------------------------------------
        # EXTENSION
        # ---------------------------------------------------------
        if file_extension:
            normalized_extension = file_extension.lower().strip()

            if normalized_extension:
                self.extensions.add(normalized_extension)

        # ---------------------------------------------------------
        # DIRECTORY
        # ---------------------------------------------------------
        if directory_type:
            normalized_directory = directory_type.lower().strip()

            if normalized_directory:
                self.directories.add(normalized_directory)

    def build_window(
        self,
        window_end: datetime | None = None,
    ):
        """
        Convert the current buffer into a behavioral-window payload.

        window_start represents the beginning of the collection
        interval.

        window_end represents the end of the collection interval.
        """

        if self.total_events == 0:
            return None

        window_start = self._normalize_timestamp(
            self.window_start
        )

        window_end = self._normalize_timestamp(
            window_end
        )

        if window_start is None:
            return None

        # If no explicit end is supplied, use the current UTC time.
        if window_end is None:
            window_end = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # SAFETY CHECK
        # ---------------------------------------------------------
        if window_end <= window_start:
            from datetime import timedelta

            window_end = window_start + timedelta(seconds=1)

        duration_seconds = (
            window_end - window_start
        ).total_seconds()

        activity_rate = (
            self.total_events / duration_seconds
        )

        sensitive_ratio = (
            self.sensitive_events / self.total_events
            if self.total_events > 0
            else 0.0
        )

        # ---------------------------------------------------------
        # AFTER-HOURS
        # ---------------------------------------------------------
        after_hours = self._is_after_hours(
            window_end
        )

        # ---------------------------------------------------------
        # OBSERVED ACTIVITY
        # ---------------------------------------------------------
        observed_activity = ",".join(
            sorted(self.observed_activities)
        )

        return {
            "window_start": window_start,
            "window_end": window_end,

            "observed_activity": observed_activity,

            "total_events": self.total_events,

            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "files_moved": self.files_moved,

            "sensitive_events": self.sensitive_events,
            "sensitive_ratio": sensitive_ratio,

            "total_data_volume": self.total_data_volume,

            "unique_extensions": len(
                self.extensions
            ),

            "directory_breadth": len(
                self.directories
            ),

            "activity_rate": activity_rate,

            "after_hours": after_hours,

            "session_id": self.session_id,
        }

    @staticmethod
    def _normalize_timestamp(
        timestamp: datetime | None,
    ) -> datetime | None:

        if timestamp is None:
            return None

        if timestamp.tzinfo is None:
            return timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(timezone.utc)

    @staticmethod
    def _is_after_hours(
        timestamp: datetime,
    ) -> bool:
        """
        Evaluate working hours in the organization's policy timezone.

        Policy:
            Monday-Friday
            09:00-18:00

        Timestamps are stored internally in UTC but converted to
        Asia/Kolkata before evaluating the policy.
        """

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        policy_time = timestamp.astimezone(
            POLICY_TIMEZONE
        )

        weekday = policy_time.weekday()

        # Saturday / Sunday
        if weekday >= 5:
            return True

        hour = policy_time.hour

        return hour < 9 or hour >= 18