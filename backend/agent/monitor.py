from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from agent.classifier import SensitiveFileClassifier


class FileActivityHandler(FileSystemEventHandler):
    """
    Converts filesystem events into normalized activity records.

    The handler does not send anything to the backend.
    It only observes, filters noise, and classifies events.

    Transport is handled separately by client.py.
    """

    # --------------------------------------------------
    # Technical / Runtime Noise
    # --------------------------------------------------

    IGNORED_EXTENSIONS = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".db-journal",
        ".db-wal",
        ".db-shm",
        ".tmp",
        ".temp",
        ".cache",
        ".log",
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
    }

    IGNORED_FILENAMES = {
        "thumbs.db",
        ".ds_store",
        "desktop.ini",
    }

    IGNORED_DIRECTORIES = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".cache",
    }

    def __init__(
        self,
        event_callback: Callable[[dict], None],
        classifier: SensitiveFileClassifier,
    ):
        super().__init__()

        self.event_callback = event_callback
        self.classifier = classifier

    # --------------------------------------------------
    # Noise Filtering
    # --------------------------------------------------

    def _is_ignored_path(self, path: Path) -> bool:
        """
        Determine whether a filesystem path represents
        technical/runtime noise that should not contribute
        to behavioral analysis.

        This prevents development/runtime activity from
        contaminating the employee behavioral baseline.
        """

        filename = path.name.lower()

        # Exact technical filenames
        if filename in self.IGNORED_FILENAMES:
            return True

        # Technical extensions
        suffix = path.suffix.lower()

        if suffix in self.IGNORED_EXTENSIONS:
            return True

        # Runtime/cache directories
        for part in path.parts:
            if part.lower() in self.IGNORED_DIRECTORIES:
                return True

        return False

    # --------------------------------------------------
    # Directory Classification
    # --------------------------------------------------

    def _directory_type(self, path: Path) -> str:
        """
        Determine the logical directory category.

        This avoids sending the complete local path
        to the backend.
        """

        path_string = str(path).lower()

        home = str(Path.home()).lower()

        if "downloads" in path_string:
            return "downloads"

        if "desktop" in path_string:
            return "desktop"

        if "documents" in path_string:
            return "documents"

        if "companyworkspace" in path_string:
            return "company_workspace"

        if home in path_string:
            return "user_directory"

        return "other"

    # --------------------------------------------------
    # Build Event
    # --------------------------------------------------

    def _build_event(
        self,
        event_type: str,
        path_string: str,
    ) -> Optional[dict]:

        path = Path(path_string)

        # Ignore directories.
        if path.is_dir():
            return None

        # Ignore technical/runtime noise.
        if self._is_ignored_path(path):
            return None

        try:
            file_size = path.stat().st_size

        except (
            FileNotFoundError,
            PermissionError,
            OSError,
        ):
            file_size = 0

        directory_type = self._directory_type(path)

        classification = self.classifier.classify(
            file_path=str(path),
            directory_type=directory_type,
        )

        return {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc),
            "file_extension": (
                path.suffix.lower() or None
            ),
            "file_size": file_size,
            "is_sensitive": classification.is_sensitive,
            "directory_type": directory_type,
        }

    # --------------------------------------------------
    # Emit Event
    # --------------------------------------------------

    def _emit(
        self,
        event_type: str,
        path_string: str,
    ):
        event = self._build_event(
            event_type,
            path_string,
        )

        if event is not None:
            self.event_callback(event)

    # --------------------------------------------------
    # File Created
    # --------------------------------------------------

    def on_created(self, event):
        if not event.is_directory:
            self._emit(
                "create",
                event.src_path,
            )

    # --------------------------------------------------
    # File Modified
    # --------------------------------------------------

    def on_modified(self, event):
        if not event.is_directory:
            self._emit(
                "modify",
                event.src_path,
            )

    # --------------------------------------------------
    # File Deleted
    # --------------------------------------------------

    def on_deleted(self, event):
        if not event.is_directory:
            self._emit(
                "delete",
                event.src_path,
            )

    # --------------------------------------------------
    # File Moved / Renamed
    # --------------------------------------------------

    def on_moved(self, event):
        if not event.is_directory:
            self._emit(
                "move",
                event.dest_path,
            )


class FileSystemMonitor:
    """
    Controls filesystem observers.

    One monitor instance can watch multiple
    configured directories.
    """

    def __init__(
        self,
        directories: list[Path],
        event_callback: Callable[[dict], None],
        classifier: SensitiveFileClassifier,
    ):
        self.directories = directories
        self.event_callback = event_callback
        self.classifier = classifier

        self.observer = Observer()

        self.handler = FileActivityHandler(
            event_callback=self.event_callback,
            classifier=self.classifier,
        )

    def start(self):
        """
        Start monitoring all configured directories.
        """

        for directory in self.directories:

            if not directory.exists():
                print(
                    f"[WARNING] Directory does not exist: "
                    f"{directory}"
                )
                continue

            if not directory.is_dir():
                print(
                    f"[WARNING] Not a directory: "
                    f"{directory}"
                )
                continue

            self.observer.schedule(
                self.handler,
                str(directory),
                recursive=True,
            )

            print(
                f"[MONITORING] {directory}"
            )

        self.observer.start()

        print(
            "[AGENT] Filesystem monitoring started."
        )

    def stop(self):
        """
        Stop filesystem monitoring cleanly.
        """

        self.observer.stop()
        self.observer.join()

        print(
            "[AGENT] Filesystem monitoring stopped."
        )