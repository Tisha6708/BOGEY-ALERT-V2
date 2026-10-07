from pathlib import Path
import os

from dotenv import load_dotenv


# --------------------------------------------------
# Environment Configuration
# --------------------------------------------------

# Load the backend/.env file when the agent is started
# from the backend project directory.
load_dotenv()


# --------------------------------------------------
# Agent Identity
# --------------------------------------------------

DEVICE_CODE = os.getenv(
    "BOGEY_DEVICE_CODE",
    "DEVICE-001",
)

DEVICE_CREDENTIAL = os.getenv(
    "BOGEY_DEVICE_CREDENTIAL",
    "",
)


# --------------------------------------------------
# Backend
# --------------------------------------------------

BACKEND_URL = os.getenv(
    "BOGEY_BACKEND_URL",
    "http://127.0.0.1:8000",
)

EVENTS_ENDPOINT = f"{BACKEND_URL}/events/"
BEHAVIOR_ENDPOINT = f"{BACKEND_URL}/behavior/windows"


# --------------------------------------------------
# Agent
# --------------------------------------------------

AGENT_VERSION = "2.0.0"

SESSION_ID = os.getenv(
    "BOGEY_SESSION_ID",
    "agent-session",
)


# --------------------------------------------------
# Filesystem Monitoring
# --------------------------------------------------

MONITORED_DIRECTORIES = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]


# --------------------------------------------------
# Event Handling
# --------------------------------------------------

EVENT_QUEUE_MAX_SIZE = 10000

SEND_BATCH_SIZE = 25

SEND_INTERVAL_SECONDS = 60


# --------------------------------------------------
# File Size Limits
# --------------------------------------------------

MAX_TRACKED_FILE_SIZE = 10 * 1024 * 1024 * 1024