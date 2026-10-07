from sqlmodel import SQLModel, Session, create_engine, text

from app.core.config import settings


connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)


def create_db_and_tables():
    """
    Create missing tables and apply lightweight development
    migrations for existing SQLite databases.
    """

    # Create tables that do not exist yet.
    SQLModel.metadata.create_all(engine)

    # Apply small schema changes to existing tables.
    with engine.connect() as connection:
        _add_missing_behavioral_window_columns(connection)


def _add_missing_behavioral_window_columns(connection):
    """
    Add columns introduced after the initial database schema.

    This keeps existing behavioral windows, alerts, employees,
    devices, and models intact.
    """

    result = connection.execute(
        text("PRAGMA table_info(behavioralwindow)")
    )

    existing_columns = {
        row[1]
        for row in result.fetchall()
    }

    if "observed_activity" not in existing_columns:
        connection.execute(
            text(
                """
                ALTER TABLE behavioralwindow
                ADD COLUMN observed_activity TEXT NOT NULL DEFAULT ''
                """
            )
        )

    connection.commit()


def get_session():
    with Session(engine) as session:
        yield session