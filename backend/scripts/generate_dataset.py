import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

random.seed(42)

OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "behavioral_dataset.csv"

WINDOWS_PER_EMPLOYEE = 90


# ============================================================
# EMPLOYEES
# ============================================================

EMPLOYEES = [
    ("EMP_001", "developer", "engineering"),
    ("EMP_002", "developer", "engineering"),
    ("EMP_003", "developer", "engineering"),
    ("EMP_004", "developer", "engineering"),

    ("EMP_005", "finance", "finance"),
    ("EMP_006", "finance", "finance"),
    ("EMP_007", "finance", "finance"),
    ("EMP_008", "finance", "finance"),

    ("EMP_009", "hr", "human_resources"),
    ("EMP_010", "hr", "human_resources"),
    ("EMP_011", "hr", "human_resources"),

    ("EMP_012", "security_analyst", "security"),
    ("EMP_013", "security_analyst", "security"),
    ("EMP_014", "security_analyst", "security"),

    ("EMP_015", "manager", "management"),
    ("EMP_016", "manager", "management"),
    ("EMP_017", "manager", "management"),
    ("EMP_018", "manager", "management"),
    ("EMP_019", "manager", "management"),
    ("EMP_020", "manager", "management"),
]


# ============================================================
# ROLE PROFILES
# ============================================================

ROLE_PROFILES = {

    "developer": {
        "events": (15, 70),
        "created": (1, 12),
        "modified": (5, 40),
        "deleted": (0, 4),
        "moved": (0, 6),
        "data_volume": (10_000, 80_000_000),
        "sensitive": (0, 2),
        "extensions": (2, 8),
        "directories": (1, 8),
        "session": (30, 180),
    },

    "finance": {
        "events": (20, 100),
        "created": (1, 12),
        "modified": (8, 55),
        "deleted": (0, 5),
        "moved": (0, 8),
        "data_volume": (20_000, 120_000_000),
        "sensitive": (2, 15),
        "extensions": (2, 10),
        "directories": (1, 10),
        "session": (30, 240),
    },

    "hr": {
        "events": (15, 80),
        "created": (1, 10),
        "modified": (5, 45),
        "deleted": (0, 4),
        "moved": (0, 6),
        "data_volume": (10_000, 70_000_000),
        "sensitive": (1, 12),
        "extensions": (2, 8),
        "directories": (1, 8),
        "session": (30, 180),
    },

    "security_analyst": {
        "events": (40, 180),
        "created": (2, 20),
        "modified": (15, 90),
        "deleted": (0, 12),
        "moved": (0, 18),
        "data_volume": (30_000, 250_000_000),
        "sensitive": (5, 40),
        "extensions": (3, 15),
        "directories": (2, 20),
        "session": (30, 360),
    },

    "manager": {
        "events": (8, 50),
        "created": (0, 7),
        "modified": (3, 25),
        "deleted": (0, 3),
        "moved": (0, 5),
        "data_volume": (5_000, 50_000_000),
        "sensitive": (0, 6),
        "extensions": (1, 6),
        "directories": (1, 6),
        "session": (20, 150),
    },
}


# ============================================================
# DATASET FIELDS
# ============================================================

FIELDS = [
    "employee_id",
    "role",
    "department",
    "timestamp",
    "files_accessed",
    "files_created",
    "files_modified",
    "files_deleted",
    "files_moved",
    "sensitive_events",
    "sensitive_file_ratio",
    "data_volume",
    "access_rate",
    "session_duration",
    "unique_resources",
    "unique_extensions",
    "directory_breadth",
    "after_hours",
    "weekend_activity",
    "is_anomaly",
    "scenario",
]


# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def recalculate_metrics(row):
    """
    Keep all dependent behavioral features consistent
    after an anomaly modifies the base activity.
    """

    operation_count = (
        row["files_created"]
        + row["files_modified"]
        + row["files_deleted"]
        + row["files_moved"]
    )

    row["files_accessed"] = max(
        row["files_accessed"],
        operation_count,
    )

    row["sensitive_file_ratio"] = round(
        row["sensitive_events"]
        / max(row["files_accessed"], 1),
        4,
    )

    row["access_rate"] = round(
        row["files_accessed"]
        / max(row["session_duration"], 1),
        4,
    )

    return row


# ============================================================
# NORMAL BEHAVIOR
# ============================================================

def generate_normal(
    employee_id,
    role,
    department,
    timestamp,
):
    profile = ROLE_PROFILES[role]

    events = random.randint(*profile["events"])

    created = random.randint(
        *profile["created"]
    )

    modified = random.randint(
        *profile["modified"]
    )

    deleted = random.randint(
        *profile["deleted"]
    )

    moved = random.randint(
        *profile["moved"]
    )

    sensitive = random.randint(
        *profile["sensitive"]
    )

    data_volume = random.randint(
        *profile["data_volume"]
    )

    session_duration = random.randint(
        *profile["session"]
    )

    extensions = random.randint(
        *profile["extensions"]
    )

    directories = random.randint(
        *profile["directories"]
    )

    weekend = timestamp.weekday() >= 5

    # Security analysts naturally have slightly more
    # after-hours activity than other roles.
    if role == "security_analyst":
        after_hours = random.random() < 0.08
    else:
        after_hours = random.random() < 0.03

    total_operations = (
        created
        + modified
        + deleted
        + moved
    )

    total_events = max(
        events,
        total_operations,
    )

    files_accessed = random.randint(
        max(total_events, 1),
        max(total_events * 2, 2),
    )

    unique_resources = random.randint(
        max(1, directories),
        max(2, directories * 3),
    )

    row = {
        "employee_id": employee_id,
        "role": role,
        "department": department,
        "timestamp": timestamp.isoformat(),

        "files_accessed": files_accessed,
        "files_created": created,
        "files_modified": modified,
        "files_deleted": deleted,
        "files_moved": moved,

        "sensitive_events": sensitive,

        "sensitive_file_ratio": round(
            sensitive / max(files_accessed, 1),
            4,
        ),

        "data_volume": data_volume,

        "access_rate": round(
            files_accessed / max(session_duration, 1),
            4,
        ),

        "session_duration": session_duration,

        "unique_resources": unique_resources,
        "unique_extensions": extensions,
        "directory_breadth": directories,

        "after_hours": after_hours,
        "weekend_activity": weekend,

        "is_anomaly": 0,
        "scenario": "normal",
    }

    return row


# ============================================================
# ANOMALY GENERATION
# ============================================================

def generate_anomaly(
    employee_id,
    role,
    department,
    timestamp,
):
    scenario = random.choice([
        "data_spike",
        "mass_modification",
        "mass_deletion",
        "sensitive_access",
        "after_hours_burst",
        "resource_burst",
    ])

    row = generate_normal(
        employee_id,
        role,
        department,
        timestamp,
    )

    # --------------------------------------------------------
    # 1. DATA SPIKE
    # --------------------------------------------------------

    if scenario == "data_spike":

        row["data_volume"] *= random.randint(
            10,
            25,
        )

        row["files_accessed"] *= random.randint(
            4,
            8,
        )

        row["unique_resources"] = max(
            row["unique_resources"],
            random.randint(20, 60),
        )

        row["directory_breadth"] = max(
            row["directory_breadth"],
            random.randint(10, 30),
        )

    # --------------------------------------------------------
    # 2. MASS MODIFICATION
    # --------------------------------------------------------

    elif scenario == "mass_modification":

        row["files_modified"] = random.randint(
            150,
            600,
        )

        row["files_accessed"] = random.randint(
            250,
            900,
        )

        row["unique_resources"] = random.randint(
            30,
            100,
        )

        row["directory_breadth"] = random.randint(
            15,
            50,
        )

        row["unique_extensions"] = random.randint(
            8,
            20,
        )

    # --------------------------------------------------------
    # 3. MASS DELETION
    # --------------------------------------------------------

    elif scenario == "mass_deletion":

        row["files_deleted"] = random.randint(
            100,
            500,
        )

        row["files_accessed"] = random.randint(
            250,
            800,
        )

        row["unique_resources"] = random.randint(
            30,
            100,
        )

        row["directory_breadth"] = random.randint(
            15,
            50,
        )

        row["data_volume"] *= random.randint(
            3,
            8,
        )

    # --------------------------------------------------------
    # 4. SENSITIVE DATA ACCESS
    # --------------------------------------------------------

    elif scenario == "sensitive_access":

        row["sensitive_events"] = random.randint(
            50,
            250,
        )

        row["files_accessed"] = random.randint(
            150,
            600,
        )

        row["data_volume"] *= random.randint(
            3,
            10,
        )

        row["unique_resources"] = random.randint(
            20,
            80,
        )

        row["directory_breadth"] = random.randint(
            10,
            40,
        )

    # --------------------------------------------------------
    # 5. AFTER-HOURS BURST
    # --------------------------------------------------------

    elif scenario == "after_hours_burst":

        row["after_hours"] = True

        row["files_accessed"] = random.randint(
            200,
            700,
        )

        row["data_volume"] *= random.randint(
            5,
            15,
        )

        row["unique_resources"] = random.randint(
            30,
            100,
        )

        row["directory_breadth"] = random.randint(
            15,
            50,
        )

    # --------------------------------------------------------
    # 6. RESOURCE BURST
    # --------------------------------------------------------

    elif scenario == "resource_burst":

        row["unique_resources"] = random.randint(
            100,
            500,
        )

        row["directory_breadth"] = random.randint(
            50,
            200,
        )

        row["unique_extensions"] = random.randint(
            15,
            30,
        )

        row["files_accessed"] = random.randint(
            300,
            900,
        )

        row["data_volume"] *= random.randint(
            3,
            8,
        )

    # --------------------------------------------------------
    # Recalculate all dependent behavioral metrics.
    # --------------------------------------------------------

    row = recalculate_metrics(row)

    row["is_anomaly"] = 1
    row["scenario"] = scenario

    return row


# ============================================================
# MAIN
# ============================================================

def main():

    rows = []

    start_date = datetime(
        2026,
        1,
        1,
        9,
        30,
        tzinfo=timezone.utc,
    )

    for employee_id, role, department in EMPLOYEES:

        employee_offset = random.randint(
            0,
            100,
        )

        for day in range(
            WINDOWS_PER_EMPLOYEE
        ):

            timestamp = (
                start_date
                + timedelta(days=day)
                + timedelta(minutes=employee_offset)
            )

            # 90% normal / 10% anomalous
            if random.random() < 0.10:

                row = generate_anomaly(
                    employee_id,
                    role,
                    department,
                    timestamp,
                )

            else:

                row = generate_normal(
                    employee_id,
                    role,
                    department,
                    timestamp,
                )

            rows.append(row)

    # Shuffle final dataset so records aren't grouped
    # by employee.
    random.shuffle(rows)

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    normal_count = sum(
        1
        for row in rows
        if row["is_anomaly"] == 0
    )

    anomaly_count = sum(
        1
        for row in rows
        if row["is_anomaly"] == 1
    )

    print("=" * 60)
    print("BOGEY-ALERT SYNTHETIC DATASET")
    print("=" * 60)

    print(
        f"Employees       : {len(EMPLOYEES)}"
    )

    print(
        f"Records         : {len(rows)}"
    )

    print(
        f"Normal          : {normal_count}"
    )

    print(
        f"Anomalies       : {anomaly_count}"
    )

    print(
        f"Output          : {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()